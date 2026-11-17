package workbench.events.l01

/**
 * One line per event for the parcel's tracking page, for example `PP-7781 collected, 2.5 kg` or
 * `PP-7781 not delivered: NOBODY_HOME`.
 *
 * TODO 5: delete the else branch, compile, and let the compiler list the cases you still need.
 */
fun summary(event: ParcelEvent): String = when (event) {
    is ParcelBooked -> "${event.parcelId} booked, ${event.weight}"
    else -> "event ${event.parcelId}"
}
