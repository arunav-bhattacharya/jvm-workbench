package workbench.injector.app.smoke

import workbench.injector.annotations.smoke.Factory

// Smoke example (keep or delete). KSP writes build/generated/ksp/smoke/kotlin/workbench/injector/app/smoke/RouteFactory.kt.
//   ./gradlew :injector:app:kspSmokeKotlin
@Factory
class Route {
    val name: String = "highway"
}
