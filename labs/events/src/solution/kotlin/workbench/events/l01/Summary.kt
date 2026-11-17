package workbench.events.l01

/**
 * One line per event for the parcel's tracking page. No `else` branch: when someone adds an
 * event type, this function stops compiling until it says what the new event looks like.
 */
fun summary(event: ParcelEvent): String = when (event) {
    is ParcelBooked -> "${event.parcelId} booked, ${event.weight}"
    is DeliveryFailed -> "${event.parcelId} not delivered: ${event.reason}"
    is ParcelCollected -> "${event.parcelId} collected, ${event.weight}"
    is ParcelDelivered -> "${event.parcelId} delivered, ${event.weight}"
}
