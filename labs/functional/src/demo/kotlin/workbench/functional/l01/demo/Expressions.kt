package workbench.functional.l01.demo

enum class AuthStatus { APPROVED, DECLINED, ERROR }

// Statement style: declare a var, then assign it in every branch and hope you didn't miss one.
fun statusStatement(httpCode: Int): AuthStatus {
    var status: AuthStatus
    if (httpCode == 200) status = AuthStatus.APPROVED
    else if (httpCode == 402) status = AuthStatus.DECLINED
    else status = AuthStatus.ERROR
    return status
}

// Expression style: the when IS the value. No var, nothing to forget, nothing to reassign later.
fun statusOf(httpCode: Int): AuthStatus = when (httpCode) {
    200 -> AuthStatus.APPROVED
    402 -> AuthStatus.DECLINED
    else -> AuthStatus.ERROR
}

// try is an expression too: the value of the try block, or the value of the catch block.
fun parseCents(raw: String): Long = try {
    raw.toLong()
} catch (e: NumberFormatException) {
    -1
}

fun main() {
    for (code in listOf(200, 402, 503)) {
        println("$code -> ${statusOf(code)} (statement version: ${statusStatement(code)})")
    }
    println("parseCents(\"1250\") = ${parseCents("1250")}")
    println("parseCents(\"12x\")  = ${parseCents("12x")}")
}
