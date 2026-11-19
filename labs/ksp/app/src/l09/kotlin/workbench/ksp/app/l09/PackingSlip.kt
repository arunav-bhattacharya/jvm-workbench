package workbench.ksp.app.l09

// Reads the packing slip that lesson 9's processor wrote into this build's resources, from the class path.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l09.PackingSlipKt
fun main() {
    val slip = Thread.currentThread().contextClassLoader.getResource("META-INF/movemate/packing-slip.txt")
        ?: error("no packing slip on the class path: run ./gradlew :ksp:app:kspL09Kotlin and look for warnings")
    println("from ${slip.path.substringAfter("/ksp/app/")}:")
    print(slip.readText())
}
