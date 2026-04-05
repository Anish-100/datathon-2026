


def make_income(income: int, zip_code: int, conn) -> int:
    """
    Compares personal income category against the ZIP code's median income 
    using a provided database connection.
    """
    cursor = conn.cursor()

    # 1. Execute the query correctly
    # Removed the trailing comma and fixed the parameterization
    query = "SELECT zip_income FROM OC_HOUSING_DETAILED_CLEANED WHERE zip_code = ?"
    cursor.execute(query, (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0 
        
    zip_income_val = result[0]

    get_cat = lambda val: (
        'a' if val < 100000 else
        'b' if val < 200000 else
        'c' if val < 500000 else
        'd'
    )

    return 1 if get_cat(income) == get_cat(zip_income_val) else 0


def make_detached_houses(count: int, zip_code: int, conn) -> int:
    """Compares detached house count against the ZIP code's detached house count."""
    cursor = conn.cursor()
    cursor.execute("SELECT Detached_Houses FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 3000 else
        'b' if val < 7000 else
        'c' if val < 12000 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_attached_houses(count: int, zip_code: int, conn) -> int:
    """Compares attached house count against the ZIP code's attached house count."""
    cursor = conn.cursor()
    cursor.execute("SELECT Attached_Houses FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 500 else
        'b' if val < 1500 else
        'c' if val < 3000 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_duplexes(count: int, zip_code: int, conn) -> int:
    """Compares duplex count against the ZIP code's duplex count."""
    cursor = conn.cursor()
    cursor.execute("SELECT Duplexes FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 50 else
        'b' if val < 200 else
        'c' if val < 500 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_small_apartments(count: int, zip_code: int, conn) -> int:
    """Compares small apartment (3-4 units) count against the ZIP code's count."""
    cursor = conn.cursor()
    cursor.execute("SELECT Small_Apartments_3_to_4 FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 200 else
        'b' if val < 700 else
        'c' if val < 1500 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_mid_apartments(count: int, zip_code: int, conn) -> int:
    """Compares mid-size apartment (5-9 units) count against the ZIP code's count."""
    cursor = conn.cursor()
    cursor.execute("SELECT Mid_Apartments_5_to_9 FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 200 else
        'b' if val < 700 else
        'c' if val < 1500 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_large_apartments(count: int, zip_code: int, conn) -> int:
    """Compares large apartment (10-19 units) count against the ZIP code's count."""
    cursor = conn.cursor()
    cursor.execute("SELECT Large_Apartments_10_to_19 FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 200 else
        'b' if val < 600 else
        'c' if val < 1200 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_major_apartments(count: int, zip_code: int, conn) -> int:
    """Compares major apartment (20-49 units) count against the ZIP code's count."""
    cursor = conn.cursor()
    cursor.execute("SELECT Major_Apartments_20_to_49 FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 200 else
        'b' if val < 600 else
        'c' if val < 1200 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_high_rise(count: int, zip_code: int, conn) -> int:
    """Compares high-rise (50+ units) count against the ZIP code's count."""
    cursor = conn.cursor()
    cursor.execute("SELECT High_Rise_50_plus FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 200 else
        'b' if val < 800 else
        'c' if val < 2000 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_total_pop(count: int, zip_code: int, conn) -> int:
    """Compares total population in units against the ZIP code's total population."""
    cursor = conn.cursor()
    cursor.execute("SELECT Total_Pop_in_Units FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 10000 else
        'b' if val < 30000 else
        'c' if val < 60000 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_pop_owners(count: int, zip_code: int, conn) -> int:
    """Compares owner-occupied population against the ZIP code's owner population."""
    cursor = conn.cursor()
    cursor.execute("SELECT Pop_Owners FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 5000 else
        'b' if val < 15000 else
        'c' if val < 30000 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_pop_renters(count: int, zip_code: int, conn) -> int:
    """Compares renter population against the ZIP code's renter population."""
    cursor = conn.cursor()
    cursor.execute("SELECT Pop_Renters FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 5000 else
        'b' if val < 15000 else
        'c' if val < 30000 else
        'd'
    )
    return 1 if get_cat(count) == get_cat(result[0]) else 0


def make_home_value_lower_quartile(value: int, zip_code: int, conn) -> int:
    """Compares home value lower quartile against the ZIP code's lower quartile."""
    cursor = conn.cursor()
    cursor.execute("SELECT Home_Value_Lower_Quartile FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 400000 else
        'b' if val < 650000 else
        'c' if val < 1000000 else
        'd'
    )
    return 1 if get_cat(value) == get_cat(result[0]) else 0


def make_home_value_median(value: int, zip_code: int, conn) -> int:
    """Compares home value median against the ZIP code's median home value."""
    cursor = conn.cursor()
    cursor.execute("SELECT Home_Value_Median FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 550000 else
        'b' if val < 800000 else
        'c' if val < 1300000 else
        'd'
    )
    return 1 if get_cat(value) == get_cat(result[0]) else 0


def make_home_value_upper_quartile(value: int, zip_code: int, conn) -> int:
    """Compares home value upper quartile against the ZIP code's upper quartile."""
    cursor = conn.cursor()
    cursor.execute("SELECT Home_Value_Upper_Quartile FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 700000 else
        'b' if val < 1000000 else
        'c' if val < 1500000 else
        'd'
    )
    return 1 if get_cat(value) == get_cat(result[0]) else 0


def make_median_year_built(year: int, zip_code: int, conn) -> int:
    """Compares median year built against the ZIP code's median year built."""
    cursor = conn.cursor()
    cursor.execute("SELECT Median_Year_Built FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
    result = cursor.fetchone()
    if result is None:
        return 0
    get_cat = lambda val: (
        'a' if val < 1960 else
        'b' if val < 1975 else
        'c' if val < 1995 else
        'd'
    )
    return 1 if get_cat(year) == get_cat(result[0]) else 0


def make_avg_household_size(size: float, zip_code: int, conn) -> int:
    """Compares average household size against the ZIP code's average household size."""
    cursor = conn.cursor()
    cursor.execute("SELECT Avg_Household_Size FROM OC_HOUSING_DETAILED_CLEANED WHERE Zip_Code = ?", (zip_code,))
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


def compute_business_viability(
    zip_code: int,
    conn,
    # --- input values ---
    income: int,
    detached_count: int,
    attached_count: int,
    duplex_count: int,
    small_apt_count: int,
    mid_apt_count: int,
    large_apt_count: int,
    major_apt_count: int,
    high_rise_count: int,
    total_pop: int,
    pop_owners: int,
    pop_renters: int,
    home_value_lower: int,
    home_value_median: int,
    home_value_upper: int,
    median_year_built: int,
    avg_household_size: float,
    # --- adjustment weights (a) — caller-supplied deltas, default 0 ---
    a_income: float = 0.0,
    a_detached: float = 0.0,
    a_attached: float = 0.0,
    a_duplexes: float = 0.0,
    a_small_apt: float = 0.0,
    a_mid_apt: float = 0.0,
    a_large_apt: float = 0.0,
    a_major_apt: float = 0.0,
    a_high_rise: float = 0.0,
    a_total_pop: float = 0.0,
    a_pop_owners: float = 0.0,
    a_pop_renters: float = 0.0,
    a_home_lower: float = 0.0,
    a_home_median: float = 0.0,
    a_home_upper: float = 0.0,
    a_year_built: float = 0.0,
    a_household_size: float = 0.0,
) -> float:
    """
    Returns a weighted business-viability score in [0, 1].

    Each feature contributes: result * (a + b)
      b = default business weight (all b values sum to 1.0)
      a = caller-supplied adjustment (positive to up-weight, negative to down-weight)

    Default weight rationale (b values):
      income              0.15  — purchasing power, always primary
      home_value_median   0.12  — neighbourhood wealth signal
      total_pop           0.10  — size of addressable market
      avg_household_size  0.08  — family composition affects spending
      detached_houses     0.07  — single-family = higher-income neighbourhoods
      pop_owners          0.06  — ownership stability / disposable income
      pop_renters         0.06  — renter density affects certain businesses
      home_value_upper    0.05  — high-end market ceiling
      home_value_lower    0.05  — affordability floor
      median_year_built   0.05  — newer stock = higher property values
      high_rise           0.05  — density signal
      attached_houses     0.04  — secondary density signal
      large_apartments    0.04  — mid-density signal
      small_apartments    0.03  — fine-grained density
      mid_apartments      0.03  — fine-grained density
      duplexes            0.02  — minor signal
      major_apartments    0.00  — not a reliable business signal by default
    """
    # Default (b) weights — must sum to 1.0
    B_INCOME        = 0.15
    B_HOME_MEDIAN   = 0.12
    B_TOTAL_POP     = 0.10
    B_HOUSEHOLD_SZ  = 0.08
    B_DETACHED      = 0.07
    B_POP_OWNERS    = 0.06
    B_POP_RENTERS   = 0.06
    B_HOME_UPPER    = 0.05
    B_HOME_LOWER    = 0.05
    B_YEAR_BUILT    = 0.05
    B_HIGH_RISE     = 0.05
    B_ATTACHED      = 0.04
    B_LARGE_APT     = 0.04
    B_SMALL_APT     = 0.03
    B_MID_APT       = 0.03
    B_DUPLEXES      = 0.02
    B_MAJOR_APT     = 0.00

    income_score        = make_income(income, zip_code, conn)
    detached_score      = make_detached_houses(detached_count, zip_code, conn)
    attached_score      = make_attached_houses(attached_count, zip_code, conn)
    duplex_score        = make_duplexes(duplex_count, zip_code, conn)
    small_apt_score     = make_small_apartments(small_apt_count, zip_code, conn)
    mid_apt_score       = make_mid_apartments(mid_apt_count, zip_code, conn)
    large_apt_score     = make_large_apartments(large_apt_count, zip_code, conn)
    major_apt_score     = make_major_apartments(major_apt_count, zip_code, conn)
    high_rise_score     = make_high_rise(high_rise_count, zip_code, conn)
    total_pop_score     = make_total_pop(total_pop, zip_code, conn)
    pop_owners_score    = make_pop_owners(pop_owners, zip_code, conn)
    pop_renters_score   = make_pop_renters(pop_renters, zip_code, conn)
    home_lower_score    = make_home_value_lower_quartile(home_value_lower, zip_code, conn)
    home_median_score   = make_home_value_median(home_value_median, zip_code, conn)
    home_upper_score    = make_home_value_upper_quartile(home_value_upper, zip_code, conn)
    year_built_score    = make_median_year_built(median_year_built, zip_code, conn)
    household_sz_score  = make_avg_household_size(avg_household_size, zip_code, conn)

    viability = (
        income_score        * (B_INCOME       + a_income)       +
        detached_score      * (B_DETACHED     + a_detached)     +
        attached_score      * (B_ATTACHED     + a_attached)     +
        duplex_score        * (B_DUPLEXES     + a_duplexes)     +
        small_apt_score     * (B_SMALL_APT    + a_small_apt)    +
        mid_apt_score       * (B_MID_APT      + a_mid_apt)      +
        large_apt_score     * (B_LARGE_APT    + a_large_apt)    +
        major_apt_score     * (B_MAJOR_APT    + a_major_apt)    +
        high_rise_score     * (B_HIGH_RISE    + a_high_rise)    +
        total_pop_score     * (B_TOTAL_POP    + a_total_pop)    +
        pop_owners_score    * (B_POP_OWNERS   + a_pop_owners)   +
        pop_renters_score   * (B_POP_RENTERS  + a_pop_renters)  +
        home_lower_score    * (B_HOME_LOWER   + a_home_lower)   +
        home_median_score   * (B_HOME_MEDIAN  + a_home_median)  +
        home_upper_score    * (B_HOME_UPPER   + a_home_upper)   +
        year_built_score    * (B_YEAR_BUILT   + a_year_built)   +
        household_sz_score  * (B_HOUSEHOLD_SZ + a_household_size)
    )

    return viability



