package workbench.events.l02.demo

// The lesson 1 hierarchy, with plain String ids and Long grams to keep the demos short.
sealed interface ParcelEvent { val parcelId: String }
data class ParcelBooked(override val parcelId: String, val grams: Long) : ParcelEvent
data class DeliveryFailed(override val parcelId: String, val reason: String) : ParcelEvent

sealed interface Handover : ParcelEvent { val grams: Long }
data class ParcelCollected(override val parcelId: String, override val grams: Long) : Handover
data class ParcelDelivered(override val parcelId: String, override val grams: Long) : Handover
