import sqlite3


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


def make_home_improvement_diy(home_improvement_diy: str, coords: int, conn) -> int:
    """
    Compares home-improvement DIY flag ('Y'/'N') against the RSM ZIP code's mode.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT HomeImprovementDIY FROM consumer_data WHERE latitude = ? AND longitude = ?", (coords[0], coords[1]))
    result = cursor.fetchone()
    if result[0] is None:
        return 0
    return 1 if home_improvement_diy == result[0] else 0


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
    pairs: list
) -> float:
    """
    pairs: list of (value, adjustment_weight) tuples in order:
        dog_owner, cat_owner, net_worth, cc_user, vehicle_count,
        owner_renter, household_size, num_children, home_improvement_diy

    Each feature contributes: result * (b + a/sum_a)
      b = default business weight (all b values sum to 1.0)
      a = caller-supplied adjustment (positive to up-weight, negative to down-weight)
    """

    (dog_owner, a_dog_owner) = pairs[0]
    (cat_owner, a_cat_owner) = pairs[1]
    (net_worth, a_net_worth) = pairs[2]
    (cc_user, a_credit_card) = pairs[3]
    (vehicle_count, a_vehicle) = pairs[4]
    (owner_renter, a_owner_renter) = pairs[5]
    (household_size, a_household_size) = pairs[6]
    (num_children, a_num_children) = pairs[7]
    (home_improvement_diy, a_home_improvement_diy) = pairs[8]

# A bit redudant but I could simplify this later on, this is a set of important usual weights
    B_DOG_OWNER     = 1
    B_CAT_OWNER     = 1
    B_OWNER_RENTER  = 20
    B_NET_WORTH     = 35
    B_HOUSEHOLD_SZ  = 15
    B_CREDIT_CARD   = 25
    B_NUM_CHILDREN  = 3
    B_VEHICLE       = 10
    B_HomeImprovementDIY = 2

    _B_TOTAL        = B_DOG_OWNER + B_CAT_OWNER + B_OWNER_RENTER + B_NET_WORTH +\
        B_HOUSEHOLD_SZ + B_CREDIT_CARD + B_NUM_CHILDREN + B_VEHICLE + B_HomeImprovementDIY
    B_DOG_OWNER     = B_DOG_OWNER     / _B_TOTAL
    B_CAT_OWNER     = B_CAT_OWNER     / _B_TOTAL
    B_OWNER_RENTER  = B_OWNER_RENTER  / _B_TOTAL
    B_NET_WORTH     = B_NET_WORTH     / _B_TOTAL
    B_HOUSEHOLD_SZ  = B_HOUSEHOLD_SZ  / _B_TOTAL
    B_CREDIT_CARD   = B_CREDIT_CARD   / _B_TOTAL
    B_NUM_CHILDREN  = B_NUM_CHILDREN  / _B_TOTAL
    B_VEHICLE       = B_VEHICLE       / _B_TOTAL

# This is the weights that are obtained from the data.
    dog_owner_score     = make_dog_owner(dog_owner, coords, conn)
    cat_owner_score     = make_cat_owner(cat_owner, coords, conn)
    net_worth_score     = make_net_worth(net_worth, coords, conn)
    credit_card_score   = make_credit_card_usage(cc_user, coords, conn)
    vehicle_score       = make_vehicle_knowledge(vehicle_count, coords, conn)
    owner_renter_score  = make_owner_renter(owner_renter, coords, conn)
    household_sz_score  = make_household_size(household_size, coords, conn)
    num_children_score  = make_num_children(num_children, coords, conn)
    home_improvement_score = make_home_improvement_diy(home_improvement_diy,coords,conn)
    sum_of_all_weights = (a_dog_owner+a_cat_owner+a_net_worth+a_credit_card+a_vehicle+a_owner_renter+a_household_size+a_num_children)

    if sum_of_all_weights<=0:
        sum_of_all_weights = 1

    viability = (
        dog_owner_score     * (B_DOG_OWNER    + (a_dog_owner/sum_of_all_weights))    +
        cat_owner_score     * (B_CAT_OWNER    + (a_cat_owner/sum_of_all_weights))    +
        net_worth_score     * (B_NET_WORTH    + (a_net_worth/sum_of_all_weights))    +
        credit_card_score   * (B_CREDIT_CARD  + (a_credit_card/sum_of_all_weights))  +
        vehicle_score       * (B_VEHICLE      + (a_vehicle/sum_of_all_weights))      +
        owner_renter_score  * (B_OWNER_RENTER + (a_owner_renter/sum_of_all_weights)) +
        household_sz_score  * (B_HOUSEHOLD_SZ + (a_household_size/sum_of_all_weights)) +
        num_children_score  * (B_NUM_CHILDREN + (a_num_children/sum_of_all_weights)) +
        home_improvement_score  * (B_HomeImprovementDIY + (a_home_improvement_diy/sum_of_all_weights))
    )

    return round(viability,3)

def save_to_file(results):
    """ Saves results to file"""
    lat_long_table = {}
    results.sort(key=lambda x: x[1], reverse=True)
    with open('API/Prediction/pretty_text.txt','w') as f:
        f.write(f"Coords -> Viability")
        f.write('\n')
        with open('API/Prediction/raw_text_2.txt','w') as f_2:
            for coords, viability in results:
                temp_str = f'{coords[0]},{coords[1]}'
                if coords in lat_long_table:
                    continue
                lat_long_table[coords]=viability
                f_2.write(temp_str)
                f_2.write('\n')
                f.write(f"{coords} -> {viability}")
                f.write('\n')


def main(pairs:list):
    conn = sqlite3.connect('API/Prediction/consumer_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT Latitude, Longitude FROM consumer_data")
    rows = cursor.fetchall()
    results = [
        (
            (lat, lon),
            compute_rsm_viability(
                coords=(lat, lon), conn=conn,
                pairs=pairs)
        )
        for lat, lon in rows
        
    ]
    save_to_file(results)



if __name__ == '__main__':
    main()