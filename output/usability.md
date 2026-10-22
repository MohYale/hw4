# Usability improvements

Four changes for the Campus Customs shop. Two are on the website, and two are in the API.

## Forgot password

The login page has a “Forgot your password?” link. The shopper enters the email on the account. The API writes a message for that address and shows the same message on the page, because this local shop has no mail server.

The message contains a link that expires in 30 minutes. The link opens a form for a new password. The new password is salted and hashed with the same settings as signup.

The message does not contain the old password. The `users` table stores `password_hash` only, so the old password cannot be looked up or emailed. A new password is what gets the shopper back into the account without putting a password in an email.

## Saved size

The login form has a size choice, from extra small through XXL. A choice is saved on the account as `users.preferred_size`. The next login can keep it or replace it.

The home page and the products page then list garments that still have that size in stock. A medium shopper sees medium pieces with a quantity above zero, not a medium that is already gone. “Show every size” opens the rest of the catalogue.

## Shipping email

A signed-in shopper can buy one piece from its product page, in a size that is still in stock and a color that product is made in. The order is stored as placed. “Mark order shipped” sets the order to shipped and writes an email to the address on the account.

The email names the order, the garment, the size, and the color. It does not contain a password. On this local shop the message is saved in `outbound_emails` and shown on the product page, so the shopper can read what would be sent when the parcel ships.

## Live stock by size and color

Inventory in the database is one quantity per product and size. Color is the list on the catalogue row, not a second stock count.

The product page reloads those size counts every few seconds, and again right after a purchase. A size at zero is marked sold out and cannot be selected. The buy request subtracts one only when that size still has a quantity above zero, in one database update, so two shoppers cannot both take the last piece. A color that is not on the product is rejected. After a sale, the count on the page is the number left.
