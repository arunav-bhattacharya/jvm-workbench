// kotlin-reflect is used only by the gen-09 demos, to show what works with and without it.
// It is always on the demo compile classpath. It is on the demo runtime classpath only when
// you pass -Preflect:
//   ./gradlew :generics:demo -Pmain=workbench.generics.l09.demo.ReflectDemoKt            (without)
//   ./gradlew :generics:demo -Pmain=workbench.generics.l09.demo.ReflectDemoKt -Preflect  (with)
// The exercises, solutions and tests never use it.
val kotlinReflect = "org.jetbrains.kotlin:kotlin-reflect:2.4.21"

dependencies {
    "demoCompileOnly"(kotlinReflect)
    if (providers.gradleProperty("reflect").isPresent) {
        "demoRuntimeOnly"(kotlinReflect)
    }
}
