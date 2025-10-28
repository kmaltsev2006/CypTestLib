def check_elements_in_a_string(
        actual_string: str,
        expected_occurrences=[],
        expected_omissions=[],
) -> list:
    wrong_data = []

    for item in expected_occurrences:
        if item not in actual_string:
            wrong_data.append((item, 'should exist'))

    for item in expected_omissions:
        if item in actual_string:
            wrong_data.append((item, 'should not exist'))

    return wrong_data
