        # 1. Open the terminal and navigate to your repository directory.
                # this is not necessary, but do the whole make dev_env and export PYTHONPATH thing 
                # I was having errors because it was temporary set 
        # 2. Run the command: export MONGO_PASSWD='designprojecta17'
        # 3. Run the command: echo $MONGO_PASSWD to verify the password is set correctly.
        # 4. Run the command: export CLOUD_MONGO=1 to set MongoDB to cloud mode.
        # run ./local.sh

        # to confirm you're connected, click the link that apprears after running ./local.sh 
        # --> mine runs on http://127.0.0.1:8000   
        # go to the PUT /people/create endpoint and try to add someone 
        # when you're adding someone, have your JSON thing look like this 
        
        # (CHANGE THE NAME BEFORE U ADD IT, BECAUSE I ALREADY ADDED THIS )
        # {
            #   "name": "Tinos",
            #   "email": "tinos@gmail.com",
            #   "affiliation": "string",
            #   "roles": "AU"
            # }
        # the email is important, I think the code checks if there's a @gmail.com 
        # the roles is also important, it only accepts one of these ['AU', 'ED', 'ME', 'CE']
            # go and checkout people.py (/data/people.py)  
            # go and checkout roles.py (/data/roles.py)

