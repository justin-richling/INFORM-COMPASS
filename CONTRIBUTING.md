## Quick Step by Step to Contributing:

#### 1) Fork this repo so you can start working in your own environment

GitHub info on Forks:

> If you want to contribute to someone else's project but don’t have permission to make changes directly, you can create your own copy of the project, make updates, and then suggest those updates for inclusion in the main project. This process is often called a "fork and pull request" workflow.
> When you create your own copy (or "fork") of a project, it’s like making a new workspace that shares code with the original project. This is useful for open-source projects or anytime you don’t have write access to the original project.

To fork the repo, navigate to the NCAR COMPASS page and find the `fork` button

![Screenshot 2025-02-26 at 9 28 06 AM (2)](https://github.com/user-attachments/assets/0d12f629-a56b-4f27-9130-0e0a510c47dc)
<br>

![Screenshot 2025-02-26 at 12 48 04 PM (2)](https://github.com/user-attachments/assets/17beb337-c69d-4cb3-8aa3-55d8904b87ad)

This will create a copy of the repo in your GitHub account. Navigate to your copy so you can clone it to your machine.

---

#### 2) Clone your repo to your local machine

![Screenshot 2025-02-26 at 9 02 56 AM (2)](https://github.com/user-attachments/assets/1e1b34fb-0361-43e3-b95b-ac14c7a2b4f9)
<br>

Navigate to where you want to house your copy of the repo. Then copy the address for your fork and in a terminal run: `git clone <copied-address>`

<img width="1001" alt="Screenshot 2025-02-26 at 12 20 32 PM" src="https://github.com/user-attachments/assets/7374e2f4-821d-44b0-8957-8ef32307ae44" />

This will create a new directory `INFORM-COMPASS-cookbook` that will be the root directory for the project. Navigate there to start making changes!

---

#### 3) Make new branch for changes/additions

When working on changes/additions, you will want to make a new branch for each proposed change in your cloned repo. Example of new branch, `small-fixes`

`git checkout -b small-fixes` will create a new branch to work from and automatically switch to it.

If you're ever unsure about which branch you're on you can do `git branch` 

<img width="453" alt="Screenshot 2025-02-26 at 10 24 41 AM" src="https://github.com/user-attachments/assets/96b7385a-518f-462d-a395-10b17addee35" />

To exit this screen just hit the q button on your keyboard

---

#### 4) Work on changes/additions to the code base/diagnostics

Now that you have a new branch and have made your changes, you'll want to push those changes to your cloned repo. There are just a few basic steps:

* Optional - Check status of changes: `git status`

<img width="692" alt="Screenshot 2025-02-26 at 10 58 05 AM" src="https://github.com/user-attachments/assets/d826c6b5-87c3-4b3c-9bbb-69aba16bb8a7" />


* Stage the changes: `git add <file>`. You will need to do this for all files that have been modified that you want to push.
  
&nbsp;&nbsp;&nbsp; If you're careful and sure all the files that have been changed are ones you want, you can do `git add *`

* Commit the changes: `git commit -m "Summary of your changes"`

&nbsp;&nbsp; This is a succinct message describing your changes. This is an important step for others to understand quickly what the changes are.

&nbsp;&nbsp; You can also just run `git commit` and it will open your default editor so you can make a more detailed message if needed.

<img width="1456" alt="Screenshot 2025-02-26 at 10 51 22 AM" src="https://github.com/user-attachments/assets/65993d57-ff69-48d2-8708-edded52b60b5" />

&nbsp;&nbsp; After saving the changes, you'll get a notification on the commit message:

<img width="686" alt="Screenshot 2025-02-26 at 10 51 36 AM" src="https://github.com/user-attachments/assets/1f7d0a49-c2a8-4ebf-9958-e0138dd22ad4" />

&nbsp;&nbsp; If you're satisfied with your changes, the final step is to push those changes to your cloned repo: `git push origin small-fixes`

---

#### 5) Submit Pull Request (PR) for review

Now that the changes have been pushed to your cloned repo, to initiate a PR, you will navigate to your GitHub repo:

![Screenshot 2025-02-26 at 11 26 27 AM (2)](https://github.com/user-attachments/assets/30f148e9-0888-44c3-8790-9c3a4a40dc29)

Clicking on the `Compare & pull request` will bring you to the NCAR COMPASS repo:

![Screenshot 2025-02-26 at 11 27 44 AM (2)](https://github.com/user-attachments/assets/432dcc35-bf55-4bf3-924a-13e0d01056f6)

Now you can add more details to the changes as well as tag people for review, people to assign the task for merging the PR, and labels for categorizing the types of changes.

---

#### 6) Wait for review. This is when the reviewer will look over the code. They may suggest changes, or add comments to your code and eventually it will get merged into the main branch!
