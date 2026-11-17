package workbench.kotlin.l06.demo

import kotlinx.serialization.SerialName
import kotlinx.serialization.SerializationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
sealed interface JobEvent {
    val jobId: String
}

@Serializable
@SerialName("queued")
data class Queued(override val jobId: String, val pages: Int, val paper: String = "A4") : JobEvent

@Serializable
@SerialName("cancelled")
data class Cancelled(override val jobId: String, val reason: String? = null) : JobEvent

private val lenient = Json { ignoreUnknownKeys = true; explicitNulls = false }

fun main() {
    val events: List<JobEvent> = listOf(Queued("job-1", 12), Cancelled("job-1"))
    val text = lenient.encodeToString(events)
    println(text)
    println("round trip equal: ${lenient.decodeFromString<List<JobEvent>>(text) == events}")

    val q = Queued("job-2", 1)
    println("static type Queued:   ${Json.encodeToString(q)}")
    println("static type JobEvent: ${Json.encodeToString<JobEvent>(q)}")

    val newer = """{"type":"queued","jobId":"job-3","pages":5,"tray":"2"}"""
    println("lenient: ${lenient.decodeFromString<JobEvent>(newer)}")
    try {
        Json.decodeFromString<JobEvent>(newer)
    } catch (e: SerializationException) {
        println("default Json: ${e.message?.lineSequence()?.first()}")
    }
    println("generated serializer: ${Queued.serializer().javaClass.name}")
}
