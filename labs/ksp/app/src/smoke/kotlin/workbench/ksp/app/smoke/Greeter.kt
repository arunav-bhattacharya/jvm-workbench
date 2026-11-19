package workbench.ksp.app.smoke

import workbench.ksp.annotations.smoke.Hello

// Smoke example (keep or delete). KSP runs the smoke processor on this source set (src/smoke) and writes
// build/generated/ksp/smoke/kotlin/workbench/ksp/app/smoke/GreeterHello.kt, which defines helloFromGreeter().
//   ./gradlew :ksp:app:kspSmokeKotlin
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.smoke.GreeterKt
@Hello
class Greeter {
    fun greet(): String = helloFromGreeter() + "!"
}

fun main() {
    println(Greeter().greet())
}
