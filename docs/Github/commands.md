Welcome to HomeAutomation!
==============================

# WORKFLOW TO IMPLEMENT SOME MODIFICATION(s)

## Getting the latest Code

    git pull <remote> <branch> # fetches the code and merges it into your working directory
    
## Create the branch

    git branch <branch-name>
    
## Implement the modifications
### Integrate all the changes in the stage
    
    git add . 
        
### Commit to backup the progress
    
    git commit

### To create the branch in the remote server and track it. Push with the -u (short for --set-upstream) option:

    git push -u origin <branch-name>

## When properly finished, checkout to the master branch

    git checkout master

## Merge the newly generated branch

    git merge <branch-name>

## Finally to push the latest code

    git push

## To delete the branch, use

    git branch -d <branch-name>

    