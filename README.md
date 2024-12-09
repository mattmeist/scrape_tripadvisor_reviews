This code will allow you to scrape reviews from TripAdvisor.

### This Script Returns:

A single csv file with all scrapable reviews for the top attractions in your stated city.

### How This Script Works:

To do so, you will need to specify a *city* and *geoId* from tripadvisor.com.
You can find this on their website. The geoId is the number that follows the "g" in the URL. 

To find this, I would search for a single attraction you are interested in, and find their geoId/city name.
For example, if I wanted to find every attraction in **Mitchell, South Dakota**:

I would search for the "Corn Palace", click on the link, and see the URL is:
https://www.tripadvisor.com/Attraction_Review-g54718-d145077-Reviews-Corn_Palace-Mitchell_South_Dakota.html

In this case, the *geoId* is "54718" and the *city_name* is "Mitchell_South_Dakota". 

To start off your python script, you would assign the variables:

geoId = 54718
city_name = "Mitchell_South_Dakota"

### Future Updates:

- Ability to scrape more than just the top attractions in a city.
- Ability to scrape Q&As
- Ability to scrape other attraction info
