### A simple tool, to keep track of prices on amazon.de/amazon.com.
This tool grew out of my need to be able to keep an eye on the price of different copmuter parts for my workstation build. 
It basically does what is stated, however I would still like to add further functionality in later releases.
I have only tested it on amazon.de, but I think it should work on other domains extensions.

##### This Tool is far from finished and still lacks a lot of basic functionalities.

##### Functionanlities still to be added:
- no item on this page ERROR
- maybe standardise product URLs after input. That means amazon. tplvldomain / sth / ASIN for every product
- notification functionality via email
    - daily/monthly update
    - update if significant price drop
    - add plots to email
- remove eval methods and change how the items are stored
- catch error between individual fetches or between updates and act accordingly, e.g. only fetch missing item again
- add documentation and better commenting
- add in_stock mechanic (maybe even how many items are left in stock)
- add a verbose option to notifier initialise / individual functions
- comparing amazons prices to other vendors
- send email if the tracker goes down due to some kind of error

