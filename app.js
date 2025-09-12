/*
	Simple router from https://stackoverflow.com/questions/55113447/node-js-http-server-routing
*/
const http = require('http');
const fs = require('fs');

const server = http.createServer((req, res) => {
	
    req.on('error', err => {
        console.error(err);
        // Handle error...
        res.statusCode = 400;
        res.end('400: Bad Request');
        return;
    });

    res.on('error', err => {
        console.error(err);
        // Handle error...
    });
	if (req.url === '/') {
		fs.readFile('./index.htm', (err, data) => {
			res.setHeader('Content-Type', 'text/html');
			res.end(data);
		})
	}else{
		fs.readFile('./' + req.url, (err, data) => {
			if(err){
				res.statusCode = 404;
				res.end('404: File Not Found');
				return
			}
			res.end(data);
		})
	}
});
server.listen(80)

setTimeout(function(){
	/*
		* IMPORTANT FUNCTION *
		Use this to show the webview, screen will remain blank until you call this function.
		Note: only available in Node.js Lab app.
	*/
	if(process.env.NODELAB === "true"){
		webAppReady();
	}
},1000)