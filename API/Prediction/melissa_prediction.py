
RSM_ZIP_CODES = (92688, 92679)


def make_dog_owner(rate: float, zip_code: int, conn) -> int:
    """
    Compares dog-owner household rate (0-100) against the RSM ZIP code's rate.
    RSM is a dog-friendly suburb; typical rate is 55-65%.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT DogOwnerRate FROM MELISSA_RSM_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 25 else
        'b' if val < 45 else
        'c' if val < 62 else
        'd'
    )
    return 1 if get_cat(rate) == get_cat(result[0]) else 0


def make_cat_owner(rate: float, zip_code: int, conn) -> int:
    """
    Compares cat-owner household rate (0-100) against the RSM ZIP code's rate.
    RSM typical rate is 3040%.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT CatOwnerRate FROM MELISSA_RSM_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 15 else
        'b' if val < 28 else
        'c' if val < 42 else
        'd'
    )
    return 1 if get_cat(rate) == get_cat(result[0]) else 0


def make_net_worth(net_worth: int, zip_code: int, conn) -> int:
    """
    Compares net worth ($) against the RSM ZIP code's median net worth.
    92688 ~$450k-700k, 92679 skews higher (~$700k+).
    """
    cursor = conn.cursor()
    cursor.execute("SELECT MedianNetWorth FROM MELISSA_RSM_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 100000 else
        'b' if val < 350000 else
        'c' if val < 650000 else
        'd'
    )
    return 1 if get_cat(net_worth) == get_cat(result[0]) else 0


def make_credit_card_usage(monthly_spend: int, zip_code: int, conn) -> int:
    """
    Compares monthly credit card spend ($) against the RSM ZIP code's median spend.
    RSM is an affluent suburb; median spend is typically $2k-4k/month.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT MedianCreditCardSpend FROM MELISSA_RSM_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 500 else
        'b' if val < 2000 else
        'c' if val < 4000 else
        'd'
    )
    return 1 if get_cat(monthly_spend) == get_cat(result[0]) else 0


def make_vehicle_knowledge(vehicle_count: int, zip_code: int, conn) -> int:
    """
    Compares number of registered vehicles per household against the RSM ZIP code's median.
    RSM is car-dependent; 2-3 vehicles per household is typical.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT MedianVehicleCount FROM MELISSA_RSM_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 1 else
        'b' if val < 2 else
        'c' if val < 3 else
        'd'
    )
    return 1 if get_cat(vehicle_count) == get_cat(result[0]) else 0


def make_owner_renter(owner_rate: float, zip_code: int, conn) -> int:
    """
    Compares owner-occupancy rate (0-100) against the RSM ZIP code's rate.
    92688 ~71% owners, 92679 ~91% owners.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT OwnerOccupancyRate FROM MELISSA_RSM_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 30 else
        'b' if val < 55 else
        'c' if val < 75 else
        'd'
    )
    return 1 if get_cat(owner_rate) == get_cat(result[0]) else 0


def make_household_size(size: float, zip_code: int, conn) -> int:
    """
    Compares average household size against the RSM ZIP code's average.
    92688 ~2.87, 92679 ~2.99 — both lean family-sized.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT AvgHouseholdSize FROM MELISSA_RSM_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 2.0 else
        'b' if val < 2.5 else
        'c' if val < 3.0 else
        'd'
    )
    return 1 if get_cat(size) == get_cat(result[0]) else 0


def make_num_children(children_per_hh: float, zip_code: int, conn) -> int:
    """
    Compares average number of children per household against the RSM ZIP code's average.
    RSM is family-oriented; typical range is 1.0-2.0 children per household.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT AvgChildrenPerHousehold FROM MELISSA_RSM_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 0.5 else
        'b' if val < 1.0 else
        'c' if val < 2.0 else
        'd'
    )
    return 1 if get_cat(children_per_hh) == get_cat(result[0]) else 0


def compute_rsm_viability(
    zip_code: int,
    conn,
    # --- input values ---
    dog_owner_rate: float,
    cat_owner_rate: float,
    net_worth: int,
    monthly_cc_spend: int,
    vehicle_count: int,
    owner_rate: float,
    household_size: float,
    children_per_hh: float,
    # --- adjustment weights (a) — caller-supplied deltas, default 0 ---
    a_dog_owner: float = 0.0,
    a_cat_owner: float = 0.0,
    a_net_worth: float = 0.0,
    a_credit_card: float = 0.0,
    a_vehicle: float = 0.0,
    a_owner_renter: float = 0.0,
    a_household_size: float = 0.0,
    a_num_children: float = 0.0,
) -> float:
    """
    Returns a weighted RSM business-viability score in [0, 1].

    Each feature contributes: result * (a + b)
      b = default business weight (all b values sum to 1.0)
      a = caller-supplied adjustment (positive to up-weight, negative to down-weight)

    Default weight rationale (b values):
      dog_owner       0.25  — pet ownership drives retail/service spend in RSM
      cat_owner       0.20  — second-highest lifestyle signal for RSM pet economy
      owner_renter    0.12  — owners spend more on home goods and local services
      net_worth       0.12  — disposable income signal
      household_size  0.10  — larger families = higher consumption
      credit_card     0.08  — active spend behaviour indicator
      num_children    0.08  — child-oriented spending (activities, food, retail)
      vehicle         0.05  — car dependency affects certain business types
    """
    B_DOG_OWNER     = 0.25
    B_CAT_OWNER     = 0.20
    B_OWNER_RENTER  = 0.12
    B_NET_WORTH     = 0.12
    B_HOUSEHOLD_SZ  = 0.10
    B_CREDIT_CARD   = 0.08
    B_NUM_CHILDREN  = 0.08
    B_VEHICLE       = 0.05

    dog_owner_score     = make_dog_owner(dog_owner_rate, zip_code, conn)
    cat_owner_score     = make_cat_owner(cat_owner_rate, zip_code, conn)
    net_worth_score     = make_net_worth(net_worth, zip_code, conn)
    credit_card_score   = make_credit_card_usage(monthly_cc_spend, zip_code, conn)
    vehicle_score       = make_vehicle_knowledge(vehicle_count, zip_code, conn)
    owner_renter_score  = make_owner_renter(owner_rate, zip_code, conn)
    household_sz_score  = make_household_size(household_size, zip_code, conn)
    num_children_score  = make_num_children(children_per_hh, zip_code, conn)

    viability = (
        dog_owner_score     * (B_DOG_OWNER    + a_dog_owner)    +
        cat_owner_score     * (B_CAT_OWNER    + a_cat_owner)    +
        net_worth_score     * (B_NET_WORTH    + a_net_worth)    +
        credit_card_score   * (B_CREDIT_CARD  + a_credit_card)  +
        vehicle_score       * (B_VEHICLE      + a_vehicle)      +
        owner_renter_score  * (B_OWNER_RENTER + a_owner_renter) +
        household_sz_score  * (B_HOUSEHOLD_SZ + a_household_size) +
        num_children_score  * (B_NUM_CHILDREN + a_num_children)
    )

    return viability
