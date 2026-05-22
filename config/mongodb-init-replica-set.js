try {
  rs.initiate({
    _id: "overleaf",
    members: [{ _id: 0, host: "mongo:27017" }]
  });
  print("Replica set initiated");
} catch (e) {
  if (e.message.match(/already initialized/)) {
    print("Replica set already initialized");
  } else {
    throw e;
  }
}
