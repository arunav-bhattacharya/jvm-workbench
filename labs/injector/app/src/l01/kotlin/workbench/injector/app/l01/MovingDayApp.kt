package workbench.injector.app.l01

// Uses the component KSP wrote during the build:
//   build/generated/ksp/l01/kotlin/workbench/injector/app/l01/GeneratedMovingDayComponent.kt
//   ./gradlew :injector:app:demo -Pmain=workbench.injector.app.l01.MovingDayAppKt
fun main() {
    val plan: MovingDayComponent = GeneratedMovingDayComponent()
    val day = plan.movingDay()
    day.plan().forEach(::println)
    println("one truck for the whole day: ${plan.truck() === day.crew.truck}")
    println("tape rolls made: ${TapeRoll.made}")
}
