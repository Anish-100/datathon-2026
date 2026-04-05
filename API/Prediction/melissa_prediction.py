import sqlite3

RSM_coordsS = (92688, 92679)


def make_dog_owner(dog_owner: str, coords: int, conn) -> int:
    """
    Compares dog-owner flag ('Y'/'N') against the RSM ZIP code's mode.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT DogOwner FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    return 1 if dog_owner == result[0] else 0


def make_cat_owner(cat_owner: str, coords: int, conn) -> int:
    """
    Compares cat-owner flag ('Y'/'N') against the RSM ZIP code's mode.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT CatOwner FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    return 1 if cat_owner == result[0] else 0


def make_net_worth(net_worth: int, coords: int, conn) -> int:
    """
    Compares net worth code (1-9) against the RSM ZIP code's median code.
    1=<$1, 2=$1-4.9k, 3=$5-14.9k, 4=$15-24.9k, 5=$25-49.9k,
    6=$50-99.9k, 7=$100-249.9k, 8=$250-499.9k, 9=$500k+
    """
    cursor = conn.cursor()
    cursor.execute("SELECT NetWorth FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 3 else
        'b' if val < 5 else
        'c' if val < 8 else
        'd'
    )
    return 1 if get_cat(net_worth) == get_cat(result[0]) else 0


def make_credit_card_usage(cc_user: str, coords: int, conn) -> int:
    """
    Compares credit card user flag ('Y'/'N') against the RSM ZIP code's mode.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT CreditCardUser FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    return 1 if cc_user == result[0] else 0


def make_vehicle_knowledge(vehicle_count: int, coords: int, conn) -> int:
    """
    Compares number of registered vehicles per household against the RSM ZIP code's median.
    RSM is car-dependent; 2-3 vehicles per household is typical.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT VehicleKnownOwnedNumber FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 1 else
        'b' if val < 2 else
        'c' if val < 3 else
        'd'
    )
    return 1 if get_cat(vehicle_count) == get_cat(result[0]) else 0


def make_owner_renter(owner_renter: str, coords: int, conn) -> int:
    """
    Compares owner/renter flag ('O'/'R') against the RSM ZIP code's mode.
    92688 ~71% owners, 92679 ~91% owners.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT OwnerRenter FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    return 1 if owner_renter == result[0] else 0


def make_household_size(size: int, coords: int, conn) -> int:
    """
    Compares household size (integer count) against the RSM ZIP code's average.
    92688 ~2.87, 92679 ~2.99 — both lean family-sized.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT HouseholdSize FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 2 else
        'b' if val < 3 else
        'c' if val < 5 else
        'd'
    )
    return 1 if get_cat(size) == get_cat(result[0]) else 0


def make_num_children(num_children: int, coords: int, conn) -> int:
    """
    Compares number of children (integer count) against the RSM ZIP code's average.
    RSM is family-oriented; typical range is 1-2 children per household.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT NumberOfChildren FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 1 else
        'b' if val < 2 else
        'c' if val < 3 else
        'd'
    )
    return 1 if get_cat(num_children) == get_cat(result[0]) else 0


def compute_rsm_viability(
    coords: int,
    conn,
    # --- input values (CSV field formats) ---
    dog_owner: str, cat_owner: str, net_worth: int, cc_user: str, vehicle_count: int,
    owner_renter: str, household_size: int, num_children: int,
    # --- adjustment weights (a) — caller-supplied deltas, default 0 ---
    a_dog_owner: float = 0.0, a_cat_owner: float = 0.0, a_net_worth: float = 0.0, a_credit_card: float = 0.0,
    a_vehicle: float = 0.0, a_owner_renter: float = 0.0, a_household_size: float = 0.0, a_num_children: float = 0.0,
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

    dog_owner_score     = make_dog_owner(dog_owner, coords, conn)
    cat_owner_score     = make_cat_owner(cat_owner, coords, conn)
    net_worth_score     = make_net_worth(net_worth, coords, conn)
    credit_card_score   = make_credit_card_usage(cc_user, coords, conn)
    vehicle_score       = make_vehicle_knowledge(vehicle_count, coords, conn)
    owner_renter_score  = make_owner_renter(owner_renter, coords, conn)
    household_sz_score  = make_household_size(household_size, coords, conn)
    num_children_score  = make_num_children(num_children, coords, conn)

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

def main():
    conn = sqlite3.connect('API/Prediction/consumer_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT Latitude, Longitude FROM consumer_data")
    rows = cursor.fetchall()
    results = [
        (
            (lat, lon),
            compute_rsm_viability(
                coords=(lat, lon), conn=conn,
                dog_owner='Y', cat_owner='N', net_worth=9,
                cc_user='Y', vehicle_count=2,
                owner_renter=0, household_size=3,
                num_children=1,
            )
        )
        for lat, lon in rows
        
    ]

    results.sort(key=lambda x: x[1], reverse=True)
    with open('API/Prediction/pretty_text.txt','w') as f:
        f.write(f"Coords -> Viability")
        f.write('\n')
        with open('API/Prediction/raw_text.txt','w') as f_2:
            f_2.write(f"Coords , Viability")
            f_2.write('\n')
            for coords, viability in results:
                f_2.write(f'{coords},{viability}')
                f_2.write('\n')
                f.write(f"{coords} -> {viability}")
                f.write('\n')

if __name__ == '__main__':
    main()