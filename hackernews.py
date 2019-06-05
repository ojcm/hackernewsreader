import argparse
import collections
import json
import logging
import requests
import sys
import validators


# Declare constants
POST_LIST_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
POST_URL = "https://hacker-news.firebaseio.com/v0/item/%d.json"
TEXT_POST_URL = "https://news.ycombinator.com/item?id=%d"

# Set up logging for debugging
logging.basicConfig(filename='hackernews.log',
                    filemode='a',
                    format=('%(asctime)s,%(msecs)d %(name)s %(levelname)s '
                            '%(message)s'),
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


class JSONHandler():
    """Class handling generic JSON methods."""

    def get_json_from_url(self, url):
        """Retrieve JSON content from given URL."""
        logging.debug("Retrieving JSON from %s" % url)

        try:
            r = requests.get(url)
        except:
            logging.exception("Error GETting from URL %s" % url)
            return None

        if (r.status_code != 200):
            logging.error("Error retrieving URL. Status code: %d." %
                          r.status_code)
            return None

        result = None
        try:
            result = r.json()
        except (ValueError):
            logging.error("No JSON found in response")

        logging.debug("Retrieved JSON: %s" % result)
        return result


class Post():
    """Representation of a single news post."""

    def __init__(self, id, rank):
        logging.debug("Initialising post #%d with id %d" % (rank, id))
        self.id = id
        self.rank = rank
        self.title = None
        self.author = None
        self.points = None
        self.comments = None
        self.uri = None

        # Use OrderedDict so we control order of elements in JSON output
        self.dict = collections.OrderedDict()

        # Retrieve additional information and build up
        self.get_details()

    def __repr__(self):
        """Return post as JSON string."""
        return json.dumps(self.as_dict(), indent=4, separators=(',', ': '))

    def get_details(self):
        """Retrieve JSON for this post and populate object."""
        post_json = self.get_post_json(self.id)
        try:
            # All expected post types have these properties.
            self.title = self.validate_string(post_json['title'])
            self.author = self.validate_string(post_json['by'])
            self.points = self.validate_int(post_json['score'])

            # 'job' posts don't have descendents.
            if post_json['type'] == 'job':
                self.comments = 0
            else:
                self.comments = self.validate_int(post_json['descendants'])

            # Some story posts don't have a 'url'.  Construct their URL from
            # their ID.
            if 'url' not in post_json:
                self.uri = TEXT_POST_URL % self.id
            else:
                self.uri = self.validate_uri(post_json['url'])

        except KeyError as e:
            # Missing JSON field.  Don't expect to hit this unless API changes.
            # We continue to execute with as much of the post as we processed
            # before the error.
            logging.exception("KeyError whilst populating Post object ID %s, "
                              "rank %d" % (self.id, self.rank))
            logging.critical(post_json)

    def validate_string(self, string):
        """Ensure string meets length requirements."""
        logging.debug("Validating string %s" % string)

        if len(string) > 256:
            logging.warning("String too long. Truncating to 256 characters.")
            string = string[:256]
        elif string == "" or string is None:
            logging.error("String is empty.")
        return string

    def validate_uri(self, uri):
        """Ensure URI is valid."""
        logging.debug("Validating URL %s" % uri)

        # Return None in error case.  This is 'null' in final output.
        try:
            if not validators.url(uri):
                uri = None
        except validators.utils.ValidationFailure:
            logging.error("Invalid URL %s" % uri)
            uri = None
        return uri

    def validate_int(self, integer):
        """Ensure value is non-negative integer."""
        logging.debug("Validating Integer")

        # Return None in error case.  This is 'null' in final output.
        if not isinstance(integer, int):
            logging.error("Non-integer provided to validate_int method.")
            integer = None
        elif integer < 0:
            logging.error("Integer is negative.")
            integer = None
        return integer

    def as_dict(self):
        """Return a representation of the post as a dictionary."""
        post_dict = {}
        post_dict['title'] = self.title
        post_dict['uri'] = self.uri
        post_dict['author'] = self.author
        post_dict['points'] = self.points
        post_dict['comments'] = self.comments
        post_dict['rank'] = self.rank
        return post_dict

    def get_post_json(self, postId):
        """Retrieve the JSON for this post ID."""
        url = POST_URL % postId
        return JSONHandler().get_json_from_url(url)


class NewsReader():
    """Main driver class.  Gathers posts and prints."""

    def __init__(self):
        self.post_ids = []

    def read_news(self, num_posts):
        """Method to retrieve and print posts."""
        self.get_post_ids(num_posts)
        self.get_and_print_news()

    def get_post_ids(self, num_posts):
        """Retrieve num_posts post IDs from Hacker News."""
        ids = JSONHandler().get_json_from_url(POST_LIST_URL)
        if ids is None:
            # If we retrieved no IDs then can't continue.  Output the error and
            # exit.
            logging.critical("No post list retrieved.")
            print("Error retrieving top posts from Hacker News.")
            sys.exit(1)
        else:
            num_retrieved = len(ids)

            # Documented behaviour of HN API is to return up to 500 posts.
            # If we don't have enough we output the error but continue with
            # what we have.
            if num_retrieved < num_posts:
                logging.error("Did not retrieve enough posts")
                logging.error("ALERT: Only displaying %d posts" %
                              num_retrieved)

            logging.debug("Retrieved %d IDs.  Required %d." %
                          (num_retrieved, num_posts))

            # Store the number of post IDs that we require.
            self.post_ids = ids[:num_posts]

    def get_and_print_news(self):
        """Initialise post for each stored ID."""
        output_list = []
        for ii in range(len(self.post_ids)):
            # Initialise post for ID at ii and get its dictionary
            # representation.
            new_post = Post(self.post_ids[ii], ii+1).as_dict()

            # Add dictionary representation to output.
            output_list.append(new_post)

        # Pretty print the posts.  ensure_ascii and encoding maintain unicode
        # characters in output.
        print(json.dumps(output_list, indent=4, separators=(',', ': ')))


class ArgParser():
    """Parse and verify command line arguments."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
                                       description='Read Hacker News in JSON.')
        self.parser.add_argument('--posts', dest='posts', action='store',
	                             type=int, required=True,
                                 help=('How many posts to print. '
                                       'A positive integer <= 100.'))

    def print_help(self):
        self.parser.print_help()

    def get_num_posts(self):
        """Retrieve and validate posts argument."""
        num_posts = self.parser.parse_args().posts

        logging.debug("Number of posts requested is %d" % num_posts)

        # Further validate the '--posts' argument.  Terminate on bad value.
        if num_posts <= 0 or num_posts > 100:
            logging.critical("Invalid number of posts: %d. Terminating." %
                             num_posts)
            self.print_help()
            sys.exit(2)

        return num_posts


if __name__ == '__main__':
    argparser = ArgParser()
    num_posts = argparser.get_num_posts()

    NewsReader().read_news(num_posts)
