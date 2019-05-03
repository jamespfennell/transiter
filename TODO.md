    
## Main development thread

TODO: add github issue to add logging configuration


printing config is broken?

1. Code quality:
    1. Clean up the code where relevant
    1. Add tests for relevant things
            -> all tests had docstring
    1. Add docs
    1. Remove all TODOs - resolve or make Github issues
    1. Document the API correctly
    1. Does the RTR app still work? Likely not!


Also need to fix the bug on the SQL Alchemy upgrade.
 Maybe it's this: https://github.com/sqlalchemy/sqlalchemy/issues/4538


The task server:
Can we run multi process and get around warnings about 123456?
Also suppress the warnings! <- This. we should support refreshing the 
feed at a smaller periodicity than the feed update takes
Workaround is to increase the refresh time

    ./taskserver/server.py
    ./taskserver/client.py
    
Models: mainly just safely renaming after we have close to 100% test coverage
Also change how short_repr works
add string repr?


DONE: 


TOGO:

    ./models/servicemapgroup.py
    ./models/servicepatternvertex.py
    ./models/servicepattern.py
    ./models/servicepatternedge.py
    ./models/routestatus.py (-> alert.py)
    ./models/feedupdate.py
    ./models/scheduledservice.py 
    ./models/scheduledtripstoptime.py
    ./models/directionnamerule.py
    ./models/scheduledtrip.py



1. Record the git hash outside of the Git repo for deployments ... 
    maybe when building the egg?
Incorporate this into building and distributing the App


Distribute the App somehow on PyPI




