package workbench.kotlin.l06

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** A sealed hierarchy: the plugin knows every subclass, so polymorphic JSON needs no extra setup. */
@Serializable
sealed interface PaymentEvent {
    val paymentId: String
}

// @SerialName fixes the "type" value, so renaming or moving a class can't change the JSON
@Serializable
@SerialName("authorized")
data class Authorized(override val paymentId: String, val amountMinor: Long, val currency: String = "EUR") : PaymentEvent

@Serializable
@SerialName("captured")
data class Captured(override val paymentId: String, val amountMinor: Long) : PaymentEvent

@Serializable
@SerialName("refunded")
data class Refunded(override val paymentId: String, val amountMinor: Long, val reason: String? = null) : PaymentEvent

/** One shared instance: Json objects are immutable and thread-safe, and reusing one is faster. */
private val eventJson = Json {
    ignoreUnknownKeys = true      // a newer producer may add fields
    explicitNulls = false         // leave out null properties instead of writing "reason": null
}

fun encodeEvents(events: List<PaymentEvent>): String = eventJson.encodeToString(events)

fun decodeEvents(text: String): List<PaymentEvent> = eventJson.decodeFromString(text)
