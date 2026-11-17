package workbench.kotlin.l06

/**
 * TODO 1: make the hierarchy serializable with kotlinx.serialization. Mark the interface and every
 * class @Serializable, and give each class a @SerialName: "queued", "printed", "jammed".
 * Imports: kotlinx.serialization.Serializable and kotlinx.serialization.SerialName.
 */
sealed interface JobEvent {
    val jobId: String
}

data class Queued(override val jobId: String, val pages: Int, val paper: String = "A4") : JobEvent

data class Printed(override val jobId: String, val pages: Int) : JobEvent

data class Jammed(override val jobId: String, val atPage: Int, val printer: String? = null) : JobEvent

/*
 * TODO 2: create ONE private Json instance, shared by both functions, that ignores unknown keys and
 * leaves out null properties (explicitNulls = false). Keep the default "type" discriminator and the
 * default encodeDefaults = false.
 */

/** TODO 3: encode the list, with a "type" field in each element. */
fun encodeEvents(events: List<JobEvent>): String = TODO("json.encodeToString(events)")

/** TODO 4: decode a list. An unknown "type" must fail with a SerializationException. */
fun decodeEvents(text: String): List<JobEvent> = TODO("json.decodeFromString(text)")
