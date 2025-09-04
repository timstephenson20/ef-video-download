IMPORTANT
***

This is a simple download utility offered to help download video content from EazyFlicks.

Absolutely no liability for any data loss caused or arising from this script or its usage is offered nor assumed. 
It is provided purely as a helping hand to retrieve your own content from EF's servers before they switch the service off and by using this script, you do so entirely at your own risk. 

This cannot make any changes to your EF account or anything stored within it. 
Video files are downloaded from the given EF Collection URL and stored in a local folder on your machine. 

Please review the code contained in run.py before you run it so that you are comfortable with what it is doing.

*** 


* Getting Started *
To setup before use, you need to install Python 3 on your machine.
To do this, follow the instructions available here: https://realpython.com/installing-python/ or just download an installer for your platform from here: https://www.python.org/downloads/

Alternatively you can also find Python in the Microsoft Store for Windows machines or install via Homebrew on a Mac.

Microsoft Store: https://apps.microsoft.com/detail/9pnrbtzxmb4z?hl=en-GB&gl=GB



Once you have Python installed, launch a command prompt / terminal / powershell window and change to the folder you've copied this project into.

In the command prompt window, type:

pip install requests

and press enter. This will add a necessary library to your new Python install to enable it to download files over the web. 

If that doesn't work, try "pip3 install requests"


Then, you're set to try downloading videos. First, you need to sign into your EazyFlicks account and create a new Collection page. 
Add all videos you want to download to this Collection and copy the URL for the page. 

Edit the file run.py using Notepad or whatever editor you prefer, and edit the line that begins "startURL" to have the address of your new collection page.
startURL = "https://eazyflicks.com/App/YOURACCOUNT/your-collection-to-download/"
 

By default, the script will place downloaded videos into a folder called "mediafiles" located wherever you have the run.py script. 
Edit the outputPath setting to change this - specify a full path to wherever you would like the video files to be saved. 

Good luck! 