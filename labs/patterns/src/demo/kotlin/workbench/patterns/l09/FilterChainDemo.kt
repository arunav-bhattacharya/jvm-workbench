package workbench.patterns.l09

// An OkHttp-style interceptor chain in front of a charge endpoint. The order of the list is behavior.

data class HttpRequest(val path: String, val headers: Map<String, String>)
data class HttpResponse(val status: Int, val body: String)

fun interface Interceptor {
    fun intercept(r: HttpRequest, next: (HttpRequest) -> HttpResponse): HttpResponse
}

// fold the interceptors into one function, from the last to the first
fun chain(interceptors: List<Interceptor>, terminal: (HttpRequest) -> HttpResponse): (HttpRequest) -> HttpResponse =
    interceptors.foldRight(terminal) { ic, next -> { r -> ic.intercept(r, next) } }

fun main() {
    var charges = 0
    val seenKeys = mutableSetOf<String?>()

    val logging = Interceptor { r, next ->
        next(r).also { println("  log: ${r.path} -> ${it.status}") }        // in: nothing; out: log the status
    }
    val auth = Interceptor { r, next ->
        if ("Authorization" in r.headers) next(r) else HttpResponse(401, "no token")   // short-circuit: stop here
    }
    val idempotency = Interceptor { r, next ->
        if (seenKeys.add(r.headers["Idempotency-Key"])) next(r) else HttpResponse(409, "duplicate")
    }
    val handler = { _: HttpRequest -> charges++; HttpResponse(200, "charged") }

    val pipeline = chain(listOf(logging, auth, idempotency), handler)

    val token = "Bearer t0k"
    println(pipeline(HttpRequest("/pay", mapOf("Authorization" to token, "Idempotency-Key" to "order-7781"))))
    println(pipeline(HttpRequest("/pay", mapOf("Authorization" to token, "Idempotency-Key" to "order-7781"))))
    println(pipeline(HttpRequest("/pay", mapOf("Idempotency-Key" to "order-7782"))))   // token missing
    println(pipeline(HttpRequest("/pay", mapOf("Authorization" to token, "Idempotency-Key" to "order-7782"))))   // fixed and retried
    println("charges: $charges")
}
