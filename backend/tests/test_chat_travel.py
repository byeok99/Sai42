"""Coordinate and transportation based chat schedule tests."""

import unittest

from app.chat.application.travel import estimate_travel_minutes
from app.common.domain.enums import Transportation


class ChatTravelTimeTest(unittest.TestCase):
    def test_same_location_has_no_travel_time(self) -> None:
        location = (36.3504, 127.3845)
        self.assertEqual(0, estimate_travel_minutes(location, location, Transportation.WALK))

    def test_selected_transportation_changes_a_longer_leg(self) -> None:
        first = (36.3504, 127.3845)
        second = (36.3704, 127.3845)
        walking = estimate_travel_minutes(first, second, Transportation.WALK)
        transit = estimate_travel_minutes(first, second, Transportation.PUBLIC_TRANSIT)
        driving = estimate_travel_minutes(first, second, Transportation.CAR)

        self.assertGreater(walking, transit)
        self.assertGreater(transit, driving)

    def test_flexible_mode_walks_short_legs_and_uses_transit_for_long_legs(self) -> None:
        origin = (36.3504, 127.3845)
        near = (36.3554, 127.3845)
        far = (36.3704, 127.3845)
        self.assertEqual(
            estimate_travel_minutes(origin, near, Transportation.WALK),
            estimate_travel_minutes(origin, near, Transportation.FLEXIBLE),
        )
        self.assertEqual(
            estimate_travel_minutes(origin, far, Transportation.PUBLIC_TRANSIT),
            estimate_travel_minutes(origin, far, Transportation.FLEXIBLE),
        )


if __name__ == "__main__":
    unittest.main()
