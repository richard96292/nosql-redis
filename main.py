import redis
from defaults import default_rooms


class Hotel:
    def __init__(self, connection: redis.Redis, hotel_name: str) -> None:
        self.r = connection
        self.hotel_name = hotel_name

        for room in default_rooms:
            key = f"{self.hotel_name}:room:{room['room_id']}"
            self.r.hset(key, mapping=room["reservation"])

    def add_room(self, room_id: int) -> None:
        key = f"{self.hotel_name}:room:{room_id}"
        self.r.hsetnx(key, "booked", 0)

    def remove_room(self, room_id: int) -> None:
        key = f"{self.hotel_name}:room:{room_id}"
        self.r.delete(key)

    def reserve_room(
        self,
        room_id: int,
        name: str,
        start_date: str,
        end_date: str,
    ) -> None:
        key = f"{self.hotel_name}:room:{room_id}"
        pipeline = self.r.pipeline()
        pipeline.watch(key)

        status = pipeline.hget(key, "booked")
        if status == "0":
            pipeline.multi()
            pipeline.hset(
                key,
                mapping={
                    "booked": 1,
                    "name": name,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )
            try:
                pipeline.execute()
            except redis.WatchError:
                print(f"Room {room_id} status changed. Try again.")
        else:
            print(f"Can't reserve room {room_id}.")

    def remove_reservation(self, room_id: int) -> None:
        key = f"{self.hotel_name}:room:{room_id}"
        pipeline = self.r.pipeline()
        pipeline.watch(key)

        status = pipeline.hget(key, "booked")
        if status == "1":
            pipeline.multi()
            pipeline.delete(key)
            pipeline.hset(key, "booked", 0)
            try:
                pipeline.execute()
            except redis.WatchError:
                print(f"Room {room_id} status changed. Try again.")
        else:
            print(f"Can't remove reservation for room {room_id}.")

    def get_room_list(self) -> ([(str, str)], [(str, str)]):
        key = f"{self.hotel_name}:room:*"
        room_hashes = self.r.keys(key)
        room_list = [self.r.hgetall(hash) for hash in room_hashes]
        available_rooms = [
            (hash, room)
            for hash, room in zip(room_hashes, room_list)
            if room["booked"] == "0"
        ]
        booked_rooms = [
            (hash, room)
            for hash, room in zip(room_hashes, room_list)
            if room["booked"] != "0"
        ]

        return (available_rooms, booked_rooms)

    def print_room_list(self, room_list: ([(str, str)], [(str, str)])) -> None:
        available_rooms, booked_rooms = room_list

        print("Available Rooms:")
        for room in available_rooms:
            print(f"Room ID: {room[0]}, Status: {room[1]['booked']}")

        print("Booked Rooms:")
        for room in booked_rooms:
            print(
                f"Room ID: {room[0]}, "
                f"Status: {room[1]['booked']}, "
                f"Name: {room[1].get('name', 'N/A')}, "
                f"Start Date: {room[1].get('start_date', 'N/A')}, "
                f"End Date: {room[1].get('end_date', 'N/A')}"
            )


def main() -> None:
    connection = redis.Redis(decode_responses=True, protocol=3)
    connection.flushdb()

    hotel = Hotel(connection, "trivago")
    hotel.add_room(404)
    hotel.add_room(405)
    hotel.remove_room(405)
    hotel.reserve_room(103, "Jeffrey Epstein", "2019-08-09", "2019-08-10")
    hotel.reserve_room(101, "Joe Biden", "2019-08-09", "2019-08-10")
    hotel.remove_reservation(103)
    hotel.remove_reservation(102)
    hotel.reserve_room(103, "Joe Biden", "2019-08-09", "2019-08-10")
    hotel.print_room_list(hotel.get_room_list())

    white_house = Hotel(connection, "white_house")
    white_house.add_room(404)
    white_house.add_room(405)
    white_house.remove_room(405)
    white_house.reserve_room(404, "Joe Biden", "2019-08-09", "2019-08-10")

    while True:
        print("\nHotel Management CLI")
        print("---------------------")
        print("1. Add Room")
        print("2. Remove Room")
        print("3. Reserve Room")
        print("4. Remove Reservation")
        print("5. Print Room List")
        print("6. Exit")
        print("---------------------")

        choice = input("Enter your choice (1-6): ")

        match choice:
            case "1":
                room_id = int(input("Enter room id: "))
                hotel.add_room(room_id)
                print(f"Room {room_id} added!")
            case "2":
                room_id = int(input("Enter room id: "))
                hotel.remove_room(room_id)
                print(f"Room {room_id} removed!")
            case "3":
                room_id = int(input("Enter room id: "))
                name = input("Enter guest name: ")
                start_date = input("Enter start date (YYYY-MM-DD): ")
                end_date = input("Enter end date (YYYY-MM-DD): ")
                hotel.reserve_room(room_id, name, start_date, end_date)
            case "4":
                room_id = int(input("Enter room id: "))
                hotel.remove_reservation(room_id)
            case "5":
                hotel.print_room_list(hotel.get_room_list())
            case "6":
                print("Goodbye!")
                break
            case _:
                print("Invalid choice! Please choose a valid option.")


if __name__ == "__main__":
    main()
