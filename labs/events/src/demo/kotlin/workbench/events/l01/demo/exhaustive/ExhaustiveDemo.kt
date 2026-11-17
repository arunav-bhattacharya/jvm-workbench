package workbench.events.l01.demo.exhaustive

sealed interface ParcelEvent { val parcelId: String }
data class ParcelBooked(override val parcelId: String, val grams: Long) : ParcelEvent
data class DeliveryFailed(override val parcelId: String, val reason: String) : ParcelEvent

sealed interface Handover : ParcelEvent { val grams: Long }
data class ParcelCollected(override val parcelId: String, override val grams: Long) : Handover
data class ParcelDelivered(override val parcelId: String, override val grams: Long) : Handover

// Step 2: uncomment this line, then run the demo again (Gradle compiles it first).
// data class ParcelLost(override val parcelId: String, val grams: Long) : ParcelEvent

/** One branch per leaf, no else: checked by the compiler. */
fun summary(e: ParcelEvent): String = when (e) {
    is ParcelBooked -> "${e.parcelId} booked, ${e.grams} g"
    is DeliveryFailed -> "${e.parcelId} not delivered: ${e.reason}"
    is ParcelCollected -> "${e.parcelId} collected, ${e.grams} g"
    is ParcelDelivered -> "${e.parcelId} delivered, ${e.grams} g"
}

/** One branch covers the whole sealed middle level, and the check still holds. */
fun changesHands(e: ParcelEvent): Boolean = when (e) {
    is Handover -> true
    is ParcelBooked, is DeliveryFailed -> false
}

/** An else branch: compiles today, and after every change anyone ever makes. */
fun label(e: ParcelEvent): String = when (e) {
    is ParcelCollected -> "pickup"
    is ParcelDelivered -> "drop-off"
    else -> "other"
}

fun main() {
    val events = listOf(
        ParcelBooked("PP-7781", 2_500),
        ParcelCollected("PP-7781", 2_500),
        ParcelDelivered("PP-7781", 2_500),
        DeliveryFailed("PP-7782", "NOBODY_HOME"),
    )
    for (e in events) println("%-36s changes hands: %-5s label: %s".format(summary(e), changesHands(e), label(e)))
}
