/*
Example Legacy Code — Node.js-era callback hell pattern (circa 2012)
TC-01 Benchmark
*/

var fs = require('fs');
var http = require('http');

function processUserData(userId, callback) {
    fs.readFile('users/' + userId + '.json', function(err, data) {
        if (err) {
            callback(err);
            return;
        }

        var user = JSON.parse(data);

        http.get('http://api.example.com/profile/' + userId, function(res) {
            var body = '';

            res.on('data', function(chunk) {
                body += chunk;
            });

            res.on('end', function() {
                var profile = JSON.parse(body);

                fs.writeFile(
                    'cache/' + userId + '.json',
                    JSON.stringify({
                        user: user,
                        profile: profile
                    }),
                    function(err) {
                        if (err) {
                            callback(err);
                            return;
                        }

                        http.get('http://api.example.com/orders/' + userId, function(res2) {
                            var body2 = '';

                            res2.on('data', function(chunk) {
                                body2 += chunk;
                            });

                            res2.on('end', function() {
                                callback(null, {
                                    user: user,
                                    profile: profile,
                                    orders: JSON.parse(body2)
                                });
                            });
                        });
                    }
                );
            });
        });
    });
}


/* ===========================
   🔥 TEST SECTION (for analyzer)
   =========================== */

var x = 10
console.log(x)
eval("alert('test')")
// TODO: refactor this function