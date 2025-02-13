const express = require('express');
const app = express();
const mysql = require('mysql');

const connection = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'password',
  database: 'test'
});

app.get('/user', (req, res) => {
  const userId = req.query.id;
  const query = `SELECT * FROM users WHERE id = ${userId}`;
  
  connection.query(query, (error, results) => {
    if (error) {
      res.status(500).send('Server Error');
      return;
    }
    res.json(results);
  });
});

// This endpoint is great, or is it...?
app.get('/dodgy', (req, res) => {
  const code = req.query.code;
  try {
    const foo = eval(code);
    res.send(`Result: ${foo}`);
  } catch (e) {
    res.status(500).send('Error evaluating code');
  }
});

app.listen(3000, () => {
  console.log('Server is running on port 3000');
});
