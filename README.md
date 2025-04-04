# 3DS Discord Rich Presence Desktop Client

*Display your 3DS game status on Discord!*

This README will be split into two sections:
  - [The quickstart guide](#quick)
  - [In-depth guide](#depth)

### Notice

*By using this app, you agree to the terms listed in [TERMS.md](/TERMS.md).*

### Credits

This project connects to a self-hosted API (or one provided by me) and fetches data received by mimicking a real 3DS connecting to the friends service and receiving friend data.  
I'd like to thank:
- [kinnay](https://github.com/kinnay) and his [NintendoClients](https://github.com/kinnay/NintendoClients)
  - NintendoClients is what this program uses to pretend to be a real 3DS.
- [hax0kartik](https://github.com/hax0kartik) and his [3dsdb](https://github.com/hax0kartik/3dsdb)
  - 3dsdb is an open-source project that includes data about games on the eShop. A modified version of it is used to retrieve the game's name and icon url.
- [HEYimHeroic](https://github.com/HEYimHeroic) and her [mii2studio](https://github.com/HEYimHeroic/mii2studio)
  - mii2studio is a command line tool written in Python that allows the user to convert between various versions of Nintendo Mii formats. I have created a modified version of it internally to convert CFSD (really, `MiiData`) to Mii Studio code.
- [jaames](https://github.com/jaames) and his [mii-qr.py](https://gist.github.com/jaames/96ce8daa11b61b758b6b0227b55f9f78)
  - mii-qr.py is a Python script that converts from the encrypted QR code format to normal CFSD. For whatever reason, a direct connection to the friends service on the 3DS returns a QR code, so this is insanely useful. Thank you.
- [qwerty](https://github.com/qwertyquerty) for her [pypresence](https://github.com/qwertyquerty/pypresence)
  - pypresence is a useful Python module that allows developers to connect their games to Discord via Python. It is how 3DS-RPC sends Rich Presence data to Discord.
- [StartBootstrap](https://github.com/StartBootstrap) for their [startbootstrap-sb-admin](https://github.com/StartBootstrap/startbootstrap-sb-admin)
  - startbootstrap-sb-admin is a template using [bootstrap](https://github.com/twbs/bootstrap) which is how I created the friends network website!
- [MrGameCub3](https://github.com/mrgamecub3) for resource design!
  - He made all of the pretty things :) -- except for the app's GUI. I did that. But the pretty logos were his!

<h1 id = 'quick'>Quickstart Guide</h1>

### Using the Desktop Client

Download the app from the [latest release](https://github.com/MCMi460/3DS-RPC/releases) and run!  
Once ran, the app will ask for you to add a friend on your Nintendo 3DS. This is for the express purpose of pulling your currently playing Nintendo game.

1. Open Discord first, and then open 3DS-RPC

2. Add the bot's friend code provided

3. Enter your own friend code when prompted

4. Profit!
  - Each update is around every ~30 seconds (keep in mind, the backend is updating at a different rate than the client, so this may vary). They are automatic, but it may take upwards of one minute after the program begins. To make certain that everything is in order, check your 3DS' friends list to verify the bot account has added you back.

<p align = 'center'>
  <img src = '/resources/tutorial.gif' alt = "Tutorial GIF (which is pronounced 'gif', not 'jif')" />
</p>

<h2 id = 'faq'>FAQ</h2>

> If none of the below Qs and As help with your problem, feel free to [file an issue](https://github.com/MCMi460/3DS-RPC/issues/new). Alternatively, you can join the [3DS-RPC Discord server](https://discord.gg/pwFASr2NKx) for a better back-and-forth method of communication with me!

<!--

***Q: This is a question?***  
**A:** And this is an answer.

-->

***Q: Whenever I play a game, 3DS-RPC won't change from the home screen!***  
**A:** Firstly, try waiting ~30 seconds, as the application has a fairly slow response time. Secondly, make sure that you've enabled "Show friends what you're playing?" on your 3DS' friends app.

*Please don't DDoS me...*

<h1 id = 'depth'>In-depth guide</h1>

<h2 id = 'building'>Building</h2>

For Windows, run
```bat
cd .\3DS-RPC\client\scripts
.\build.bat
```
For MacOS, run
```sh
cd ./3DS-RPC/client/scripts
chmod +x build.sh
./build.sh
```

\*(Make sure you have `python3` and `pip` installed)

<h2 id = 'understanding'>Understanding</h2>

The intricacies of this project are deep and innumerable. I started this project some weeks before October 16th (at least since [kinnay/NintendoClients#88](https://github.com/kinnay/NintendoClients/pull/88)), when I published the first commit on this repository. I have records of the sheer amount of pain I have undergone to create this (see [2d1ad37](https://github.com/MCMi460/3DS-RPC/commit/2d1ad3737869dfbe5dc020b496a97cf745c5f6d9), [everything on Feb 11th](https://github.com/MCMi460/3DS-RPC/commits?author=MCMi460&since=2023-02-11&until=2023-02-11), [this *thing*](https://github.com/MCMi460/3DS-RPC/commit/e6ae017e69aa82bfed2e5a02f17635de492e0d65), and [oh so much more](https://github.com/MCMi460/3DS-RPC/commits/main)), but somehow, I prevailed.

Anywho, none of this matters for the in-depth 'guide'. **If you are looking at this guide because you can't figure something out or are having an error**, *please check the [FAQ](#faq), [join my Discord server](https://discord.gg/pwFASr2NKx), or [file an issue](https://github.com/MCMi460/3DS-RPC/issues/new).* Instead, we're going to be looking at the inner-workings of the project.

So sit back, relax, and wait because, chances are, this guide is either unfinished or out-of-date.

<details>
  <summary><h3>The Beast</h3></summary>

  Let's get to the good part, shall we?

  Basic control structure:

  ![just a diagram](/resources/diagram.png)

</details>

[cli]: /client/client.py
[api]: /api/love.py
[app]: /client/app.py
[front]: /server/server.py
[back]: /server/backend.py
