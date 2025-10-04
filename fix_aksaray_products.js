// MongoDB Update Script to Fix Aksaray Business Product Assignments
// Run this in MongoDB shell or via database admin

use kuryecini_database;

db.products.updateOne({id: "c9b086ca-bad8-4bf9-9b76-ef040a807610"}, {$set: {business_id: "68dfd5805b9cea03202ec133", business_name: "başer"}});
// Updated: Başer Özel Döner -> başer

db.products.updateOne({id: "b8f22e1f-8c85-4af4-8f0d-d337d5c12a05"}, {$set: {business_id: "68dfd5805b9cea03202ec133", business_name: "başer"}});
// Updated: Pide - Kıymalı -> başer

db.products.updateOne({id: "c19b2968-feac-4b44-84a8-37e927bae236"}, {$set: {business_id: "68dfd5805b9cea03202ec133", business_name: "başer"}});
// Updated: Ayran -> başer

db.products.updateOne({id: "d59c5f31-1df4-4370-80dd-78f201ffe2f9"}, {$set: {business_id: "68dfd5805b9cea03202ec133", business_name: "başer"}});
// Updated: Baklava -> başer

db.products.updateOne({id: "1f09e409-0b2f-4e5e-9d77-9380c43855a9"}, {$set: {business_id: "68dff078b2a4ee4b6c94e2b0", business_name: "işletmew"}});
// Updated: İşletme Burger -> işletmew

db.products.updateOne({id: "7af132c5-5aab-48f1-918a-a7c8f01832bb"}, {$set: {business_id: "68dff078b2a4ee4b6c94e2b0", business_name: "işletmew"}});
// Updated: Patates Kızartması -> işletmew

db.products.updateOne({id: "dd6115d4-f650-4575-93f1-7960352d16d1"}, {$set: {business_id: "68dff078b2a4ee4b6c94e2b0", business_name: "işletmew"}});
// Updated: Coca Cola -> işletmew

db.products.updateOne({id: "c065a3d2-0901-4550-9e55-d0a2cecd8532"}, {$set: {business_id: "68e108702fbb73108f2fddb8", business_name: "Aksaray Kebap Evi"}});
// Updated: Adana Kebap -> Aksaray Kebap Evi

db.products.updateOne({id: "21235420-76d9-496a-82c5-cb62b2b4e6ee"}, {$set: {business_id: "68e108702fbb73108f2fddb8", business_name: "Aksaray Kebap Evi"}});
// Updated: Urfa Kebap -> Aksaray Kebap Evi

db.products.updateOne({id: "8926e838-adf2-49d6-9478-08edda26ef3d"}, {$set: {business_id: "68e108702fbb73108f2fddb8", business_name: "Aksaray Kebap Evi"}});
// Updated: Lahmacun -> Aksaray Kebap Evi

db.products.updateOne({id: "2789880c-9f5e-4ad8-8681-8861aa30f06e"}, {$set: {business_id: "68e108702fbb73108f2fddb8", business_name: "Aksaray Kebap Evi"}});
// Updated: Künefe -> Aksaray Kebap Evi

db.products.updateOne({id: "af57b51d-3454-40cf-9597-54f58c5e1cee"}, {$set: {business_id: "68e108702fbb73108f2fddb9", business_name: "Aksaray Pizza Palace"}});
// Updated: Margherita Pizza -> Aksaray Pizza Palace

db.products.updateOne({id: "b3de86ac-4d46-4211-ab56-1b8f5de2f5ac"}, {$set: {business_id: "68e108702fbb73108f2fddb9", business_name: "Aksaray Pizza Palace"}});
// Updated: Pepperoni Pizza -> Aksaray Pizza Palace

db.products.updateOne({id: "61e8ac5a-9621-4ded-8f77-6953194dfd8a"}, {$set: {business_id: "68e108702fbb73108f2fddb9", business_name: "Aksaray Pizza Palace"}});
// Updated: Karışık Pizza -> Aksaray Pizza Palace

db.products.updateOne({id: "b4a3c841-33a2-4426-9df6-23a50dff479e"}, {$set: {business_id: "68e108702fbb73108f2fddb9", business_name: "Aksaray Pizza Palace"}});
// Updated: Garlic Bread -> Aksaray Pizza Palace
