package workbench.kotlin.l06

/**
 * TODO 1: make the hierarchy serializable with kotlinx.serialization. Mark the interface and every
 * class @Serializable, and give each class a @SerialName: "authorized", "captured", "refunded".
 * Imports: kotlinx.serialization.Serializable and kotlinx.serialization.SerialName.
 */
sealed interface PaymentEvent {
    val paymentId: String
}

data class Authorized(override val paymentId: String, val amountMinor: Long, val currency: String = "EUR") : PaymentEvent

data class Captured(override val paymentId: String, val amountMinor: Long) : PaymentEvent

data class Refunded(override val paymentId: String, val amountMinor: Long, val reason: String? = null) : PaymentEvent

/*
 * TODO 2: create ONE private Json instance, shared by both functions, that ignores unknown keys and
 * leaves out null properties (explicitNulls = false). Keep the default "type" discriminator and the
 * default encodeDefaults = false.
 */

/** TODO 3: encode the list, with a "type" field in each element. */
fun encodeEvents(events: List<PaymentEvent>): String = TODO("json.encodeToString(events)")

/** TODO 4: decode a list. An unknown "type" must fail with a SerializationException. */
fun decodeEvents(text: String): List<PaymentEvent> = TODO("json.decodeFromString(text)")
