var request = require("request");

describe("Hello World Test", function() {
  // This is your test bundle

  describe("GET SO", function() {
    //This is testing that http GET works

    it("Checks if SO is online", function() {
      // This is description of your test - this is what you get when it fails
      
      request.get("http://stackoverflow.com/", function(error, response, body) {
        // this is your test body

        expect(response.statusCode).toBe(200);
        // this is your test assertion - it expects status code to be '200'
      });
    });
  });
});