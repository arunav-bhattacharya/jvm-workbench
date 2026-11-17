package workbench.kotlin.l06

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** A sealed hierarchy: the plugin knows every subclass, so polymorphic JSON needs no extra setup. */
@Serializable
sealed interface JobEvent {
    val jobId: String
}

// @SerialName fixes the "type" value, so renaming or moving a class can't change the JSON
@Serializable
@SerialName("queued")
data class Queued(override val jobId: String, val pages: Int, val paper: String = "A4") : JobEvent

@Serializable
@SerialName("printed")
data class Printed(override val jobId: String, val pages: Int) : JobEvent

@Serializable
@SerialName("jammed")
data class Jammed(override val jobId: String, val atPage: Int, val printer: String? = null) : JobEvent

/** One shared instance: Json objects are immutable and thread-safe, and reusing one is faster. */
private val eventJson = Json {
    ignoreUnknownKeys = true      // a newer version of the app may add fields
    explicitNulls = false         // leave out null properties instead of writing "printer": null
}

fun encodeEvents(events: List<JobEvent>): String = eventJson.encodeToString(events)

fun decodeEvents(text: String): List<JobEvent> = eventJson.decodeFromString(text)
