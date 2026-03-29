from sim_server.core.namelist import bool2txt, list2txt, num2txt, str2txt


def fmt(v, to_nml=num2txt, line_length=20, indent="    "):
    return list2txt(v, to_nml, line_length=line_length, indent=indent)


def test_single_item():
    assert fmt([1]) == "1"


def test_all_on_one_line():
    # "1, 2, 3" = 7 chars, fits in 20
    assert fmt([1, 2, 3]) == "1, 2, 3"


def test_no_trailing_comma_on_last_line():
    result = fmt([1, 2, 3, 4, 5, 6, 7, 8])
    assert not result.splitlines()[-1].rstrip().endswith(",")


def test_flushed_lines_end_with_comma():
    result = fmt([1, 2, 3, 4, 5, 6, 7, 8])
    lines = result.splitlines()
    for line in lines[:-1]:
        assert line.rstrip().endswith(",")


def test_wraps_at_line_length():
    # "1, 2, 3, 4, 5, 6, 7" = 19 fits; adding ", 8" = 23 > 20 → wraps
    result = fmt([1, 2, 3, 4, 5, 6, 7, 8])
    lines = result.splitlines()
    assert len(lines) == 2
    assert lines[0] == "1, 2, 3, 4, 5, 6, 7,"
    assert lines[1] == "    8"


def test_indent_applied_on_continuation():
    result = fmt([1, 2, 3, 4, 5, 6, 7, 8], indent="  ")
    lines = result.splitlines()
    assert lines[1].startswith("  ")
    assert not lines[1].startswith("   ")


def test_strings():
    # "'ab', 'cd'" = 10 fits; + ", 'ef'" = 17 > 15 → wraps
    result = list2txt(["ab", "cd", "ef"], str2txt, line_length=15)
    lines = result.splitlines()
    assert lines[0] == "'ab', 'cd',"
    assert "'ef'" in lines[1]


def test_bools():
    assert fmt([True, False, True], to_nml=bool2txt) == "T, F, T"


def test_multiple_wraps():
    # flushed lines get a trailing "," so can be line_length + 1; last line has no comma
    result = fmt(list(range(1, 20)), line_length=10)
    lines = result.splitlines()
    for line in lines[:-1]:
        assert len(line) <= 11  # content ≤ 10, plus trailing ","
    assert len(lines[-1]) <= 10
