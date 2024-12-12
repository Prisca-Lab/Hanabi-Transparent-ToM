from furhat_remote_api import FurhatRemoteAPI


class FurhatController:
    def __init__(self, ip, gameChoice, voice):
        self.furhat = None
        self.ip = ip
        self.gameChoice = gameChoice
        self.voice = voice

    def connect(self):
        if not self.furhat:
            self.furhat = FurhatRemoteAPI(self.ip)
            # Set voice and any other initial configurations here
            self.furhat.set_voice(name=self.voice)  # 'Adriano-Neural', 'Bianca', 'Bianca-Neural', 'Giorgio', o 'Carla'

    def say_something(self, text):
        if not self.furhat:
            raise Exception("Furhat not connected. Call connect() first.")

        # TODO: Use the following instructions when using the physical robot. Virtualenv has no camera option
        # if self.gameChoice == "ToM_Human":
            # Wait for the human player...
            # users = controller.get_users()
            # print("List of users:", users)
            # controller.attend_closest_user()

        # Note: furhat can only block execution for 60 seconds
        self.furhat.say(text=text, blocking=True)  # abort=True to abort current speaking

    def get_users(self):
        if not self.furhat:
            raise Exception("Furhat not connected. Call connect() first.")

        return self.furhat.get_users()

    def attend_closest_user(self):
        if not self.furhat:
            raise Exception("Furhat not connected. Call connect() first.")

        # Attend the user closest to the robot
        self.furhat.attend(user="CLOSEST")


"""
# Example usage
if __name__ == "__main__":
    controller = FurhatController("localhost", "ToM_Human", "Adriano-Neural")
    controller.connect()

    # Now you can perform actions with Furhat (execution will be paused when saying something)
    controller.say_something("Ciao Carmine, questo è un esempio di spiegazione.")
"""
