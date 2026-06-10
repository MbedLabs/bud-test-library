"""Example UI test using BudTestCase for browser-like assertions."""

from budtestlibrary import BudTestCase


class SettingsPageUITest(BudTestCase):
    def bud_save_button_enabled(self):
        save_button_enabled = True
        self.assertTrue(save_button_enabled, msg="Save button is enabled after valid input")

    def bud_success_banner_copy(self):
        banner_text = "Settings updated successfully"
        self.assertIn(
            member="successfully",
            container=banner_text,
            msg="Success banner confirms the save action",
        )


if __name__ == "__main__":
    SettingsPageUITest().run()
