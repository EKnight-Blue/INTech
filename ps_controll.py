from controller import Controller


if __name__ == '__main__':
    c = Controller()
    c.start()
    try:
        while True:
            for ev in c.get_events():
                print(ev)
    except KeyboardInterrupt:
        c.terminate()
