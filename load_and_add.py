from Tracker import Tracker

PATH = input("Input PATH of the Tracker you want to load. ")

tracker = Tracker(PATH, load=True)
tracker.add_items_via_input()
tracker.save()

ans = input("Do you want to deploy the tracker [Yes/No]: ")

if "y" in ans.lower():
    tracker.deploy()
