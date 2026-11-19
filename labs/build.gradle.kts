import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension

plugins {
    kotlin("jvm") version "2.4.21" apply false
    kotlin("plugin.serialization") version "2.4.21" apply false
    kotlin("plugin.allopen") version "2.4.21" apply false
    kotlin("plugin.noarg") version "2.4.21" apply false
    // the KSP Gradle plugin, applied only to the :ksp:app and :injector:app playgrounds (see processorLab below);
    // keep this version equal to versions["ksp"]
    id("com.google.devtools.ksp") version "2.3.14" apply false
}

val versions = mapOf(
    "junit" to "6.1.3",
    "assertj" to "3.27.7",
    "coroutines" to "1.11.0",
    "reactor" to "3.8.8",
    "jmh" to "1.37",
    "bytebuddy" to "1.18.17",
    "netty" to "4.2.20.Final",
    "vertx" to "5.2.3",
    "jetty" to "12.1.14",
    "slf4j" to "2.0.20",
    "jol" to "0.17",
    "serialization" to "1.12.0",
    // the KSP track and its capstone (processorLab below)
    "ksp" to "2.3.14",
    "kotlinpoet" to "2.4.0",
    "kctfork" to "0.14.0",
)
extra["versions"] = versions

subprojects {
    apply(plugin = "org.jetbrains.kotlin.jvm")

    repositories { mavenCentral() }

    val sourceSets = extensions.getByType<SourceSetContainer>()
    val main = sourceSets["main"]
    // the reference answers: same class names and signatures as the exercises in src/main
    val solution = sourceSets.create("solution")
    // small programs for the "Try it" steps, run with ./gradlew :<track>:demo -Pmain=<class>
    val demo = sourceSets.create("demo")

    configurations["solutionImplementation"].extendsFrom(configurations["implementation"])
    configurations["solutionRuntimeOnly"].extendsFrom(configurations["runtimeOnly"])
    configurations["demoImplementation"].extendsFrom(configurations["implementation"])
    configurations["demoRuntimeOnly"].extendsFrom(configurations["runtimeOnly"])

    dependencies {
        "testImplementation"(platform("org.junit:junit-bom:${versions["junit"]}"))
        "testImplementation"("org.junit.jupiter:junit-jupiter")
        "testImplementation"("org.assertj:assertj-core:${versions["assertj"]}")
        "testRuntimeOnly"("org.junit.platform:junit-platform-launcher")
    }

    extensions.configure<JavaPluginExtension> {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
    tasks.withType<JavaCompile>().configureEach {
        options.release.set(21)
        options.encoding = "UTF-8"
    }
    extensions.configure<KotlinJvmProjectExtension> {
        compilerOptions { jvmTarget.set(JvmTarget.JVM_21) }
    }

    fun Test.common() {
        useJUnitPlatform()
        // a deadlocked test fails after 20 s instead of hanging the build
        systemProperty("junit.jupiter.execution.timeout.default", "20 s")
        systemProperty("junit.jupiter.execution.timeout.thread.mode.default", "SEPARATE_THREAD")
        jvmArgs("-XX:+EnableDynamicAgentLoading", "-Xshare:off")
        testLogging {
            events("passed", "failed", "skipped")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
            showStandardStreams = false
        }
        outputs.upToDateWhen { false }
    }

    // ./gradlew :<track>:test runs the tests against YOUR code in src/main
    tasks.named<Test>("test") { common() }

    // ./gradlew :<track>:solutionTest runs the same tests against the reference answers
    tasks.register<Test>("solutionTest") {
        description = "Runs the track's tests against the reference solutions."
        group = "verification"
        common()
        val testSet = sourceSets["test"]
        testClassesDirs = testSet.output.classesDirs
        classpath = testSet.output + solution.output + configurations["testRuntimeClasspath"]
    }

    tasks.register<JavaExec>("demo") {
        description = "Runs a demo: ./gradlew :<track>:demo -Pmain=fully.qualified.MainClass [-Pargs='a b']"
        group = "application"
        classpath = demo.runtimeClasspath
        mainClass.set(providers.gradleProperty("main").orElse("missing.PassMainWithDashPmain"))
        args = providers.gradleProperty("args").map { it.split(" ").filter(String::isNotBlank) }.getOrElse(emptyList())
        jvmArgs("-Xshare:off")
        standardInput = System.`in`
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Processor labs: the KSP track (labs/ksp) and its capstone (labs/injector). brief/outlines/ksp-labs.md explains
// them for lesson writers. Each lab is three projects:
//   :<lab>              the processors: src/main (yours), src/solution (reference), src/test (kctfork), src/demo
//   :<lab>:annotations  plain Kotlin annotations the processors look for
//   :<lab>:app          an ordinary consumer that runs the processors in a real build with the KSP Gradle plugin
// A "unit" is a lesson (l01, l02, ...) or the smoke example. Adding a unit needs no edit to any Gradle file:
//   - :<lab> finds every src/{main,solution}/resources/workbench/<lab>/<unit>/SymbolProcessorProvider (one provider
//     class per line) and builds two small processor jars for that unit, <unit>MineJar from src/main and
//     <unit>SolutionJar from src/solution. Each holds only workbench/<lab>/<unit>/**, with that file moved to
//     META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider.
//   - :<lab>:app makes one source set per folder src/<unit> (src/l02/kotlin, ...). KSP runs on it with that unit's
//     processor jar plus the units listed in src/<unit>/processors.txt, and with the processor options in
//     src/<unit>/ksp.properties. One test source set (src/test) sees every unit's classes.
// Which jar: the solution by default, so the app always builds. -Pprocessors=mine uses yours (src/main) for every
// unit; -Pmine=l02,l04 uses yours for just those units. The :<lab> demos follow the same switch.
// ---------------------------------------------------------------------------------------------------------------
val processorUnit = Regex("l\\d\\d|smoke")
val processorsFlavour: String = providers.gradleProperty("processors").getOrElse("solution")
require(processorsFlavour == "solution" || processorsFlavour == "mine") {
    "-Pprocessors must be 'solution' (the default) or 'mine', not '$processorsFlavour'"
}
val mineUnits: Set<String> = providers.gradleProperty("mine").getOrElse("")
    .split(',', ' ').map(String::trim).filter(String::isNotEmpty).toSet()
mineUnits.forEach { require(it.matches(processorUnit)) { "-Pmine takes units such as l02,l04 or smoke, not '$it'" } }
fun usesMine(unit: String) = processorsFlavour == "mine" || unit in mineUnits

fun processorLab(lab: String) {
    val providerFile = "SymbolProcessorProvider"
    val services = "META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider"
    fun capability(unit: String, flavour: String) = "workbench.$lab.processors:$unit-$flavour"
    fun String.cap() = replaceFirstChar(Char::titlecase)

    // the units with a processor, read from the folders on disk
    val processorProject = project(":$lab")
    fun unitsIn(sourceSet: String) = processorProject.file("src/$sourceSet/resources/workbench/$lab")
        .listFiles().orEmpty()
        .filter { it.name.matches(processorUnit) && it.resolve(providerFile).isFile }
        .map { it.name }.toSet()
    val mineHas = unitsIn("main")
    val solutionHas = unitsIn("solution")
    for (unit in mineHas + solutionHas) {
        val missing = if (unit in mineHas) "solution" else "main"
        require(unit in mineHas && unit in solutionHas) {
            "labs/$lab/src/$missing/resources/workbench/$lab/$unit/$providerFile is missing: every processor unit " +
                "needs that file in both src/main and src/solution"
        }
    }
    val processorUnits = mineHas.sorted()

    project(":$lab") {
        val sourceSets = the<SourceSetContainer>()
        dependencies {
            "implementation"("com.google.devtools.ksp:symbol-processing-api:${versions["ksp"]}")
            "implementation"("com.squareup:kotlinpoet:${versions["kotlinpoet"]}")
            "implementation"("com.squareup:kotlinpoet-ksp:${versions["kotlinpoet"]}")
            "implementation"(project(":$lab:annotations"))
            // kctfork compiles Kotlin source strings in memory with a KSP2 processor (tests and demos)
            for (cfg in listOf("testImplementation", "demoImplementation")) {
                cfg("dev.zacsweers.kctfork:core:${versions["kctfork"]}")
                cfg("dev.zacsweers.kctfork:ksp:${versions["kctfork"]}")
            }
            // the demos run the reference processors, so a Try-it works before you finish the lab;
            // -Pprocessors=mine (or -Pmine naming the unit of -Pmain) runs yours instead
            val demoUnit = providers.gradleProperty("main").orNull
                ?.let { Regex("workbench\\.$lab\\.(l\\d\\d|smoke)\\.").find(it)?.groupValues?.get(1) }
            val demoMine = processorsFlavour == "mine" || (demoUnit != null && demoUnit in mineUnits)
            "demoImplementation"(sourceSets[if (demoMine) "main" else "solution"].output)
        }
        // kctfork 0.14.0 was built against KSP 2.3.12; keep every KSP artifact on the version the processors use,
        // so symbol-processing-api, symbol-processing, -common-deps and -aa-embeddable always match
        configurations.configureEach {
            resolutionStrategy.eachDependency {
                if (requested.group == "com.google.devtools.ksp") {
                    useVersion(versions.getValue("ksp"))
                    because("one KSP version for the API and the kctfork runtime")
                }
            }
        }
        // kctfork's KotlinCompilation is marked @ExperimentalCompilerApi; opt in once for tests and demos
        tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
            if (name == "compileTestKotlin" || name == "compileDemoKotlin") {
                compilerOptions.optIn.add("org.jetbrains.kotlin.compiler.plugin.ExperimentalCompilerApi")
            }
        }
        // the Kotlin compiler inside kctfork leaves a non-daemon thread running, so a demo that compiles in memory
        // would never exit: the demo task starts -Pmain through src/demo/.../DemoLauncher.kt, which exits after it
        tasks.named<JavaExec>("demo") {
            val demoMain = providers.gradleProperty("main").getOrElse("missing.PassMainWithDashPmain")
            mainClass.set("workbench.$lab.DemoLauncher")
            setArgs(listOf(demoMain) + args.orEmpty())
        }
        // kctfork works in build/kctfork/<task>/ (see KspCompile.kt in src/test): open it to read what was generated
        tasks.withType<Test>().configureEach {
            val dir = layout.buildDirectory.dir("kctfork/$name").get().asFile
            systemProperty("kctfork.dir", dir.absolutePath)
            doFirst { dir.deleteRecursively() }
        }

        // two processor jars per unit, each published as its own variant for :<lab>:app to ask for by capability
        for (unit in processorUnits) for (flavour in listOf("mine", "solution")) {
            val set = sourceSets[if (flavour == "mine") "main" else "solution"]
            val jar = tasks.register<Jar>("$unit${flavour.cap()}Jar") {
                description = "The $unit processor from src/${set.name}, as KSP loads it in :$lab:app."
                group = "build"
                archiveFileName.set("$lab-$unit-$flavour.jar")
                destinationDirectory.set(layout.buildDirectory.dir("processors"))
                from(set.output) {
                    include("workbench/$lab/$unit/**")
                    exclude("workbench/$lab/$unit/$providerFile")
                }
                from(set.output) {
                    include("workbench/$lab/$unit/$providerFile")
                    eachFile { path = services }
                }
                includeEmptyDirs = false
            }
            configurations.consumable("$unit${flavour.cap()}Processor") {
                description = "The $unit processor jar from src/${set.name} with its runtime dependencies."
                // dependencies of the jar: KotlinPoet, the KSP API, the annotations project, the stdlib
                extendsFrom(configurations[set.implementationConfigurationName], configurations[set.runtimeOnlyConfigurationName])
                attributes {
                    attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage.JAVA_RUNTIME))
                    attribute(Category.CATEGORY_ATTRIBUTE, objects.named(Category.LIBRARY))
                    attribute(LibraryElements.LIBRARY_ELEMENTS_ATTRIBUTE, objects.named(LibraryElements.JAR))
                    attribute(Bundling.BUNDLING_ATTRIBUTE, objects.named(Bundling.EXTERNAL))
                }
                outgoing.capability("${capability(unit, flavour)}:1.0")
                outgoing.artifact(jar)
            }
        }
    }

    project(":$lab:app") {
        apply(plugin = "com.google.devtools.ksp")
        val sourceSets = the<SourceSetContainer>()
        dependencies { "implementation"(project(":$lab:annotations")) }

        val appUnits = file("src").listFiles().orEmpty()
            .filter { it.isDirectory && it.name.matches(processorUnit) }.map { it.name }.sorted()
        for (unit in appUnits) {
            val set = sourceSets.create(unit)
            configurations[set.implementationConfigurationName].extendsFrom(configurations["implementation"])
            configurations[set.runtimeOnlyConfigurationName].extendsFrom(configurations["runtimeOnly"])

            // which processors run on src/<unit>: its own (if it has one) plus the ones processors.txt names
            val listed = file("src/$unit/processors.txt").takeIf { it.isFile }?.readLines().orEmpty()
                .map { it.substringBefore('#') }.flatMap { it.split(',', ' ', '\t') }.filter(String::isNotBlank)
            for (other in listed) {
                require(other in processorUnits) {
                    "labs/$lab/app/src/$unit/processors.txt names '$other', but labs/$lab has no " +
                        "src/main/resources/workbench/$lab/$other/$providerFile"
                }
            }
            val wanted = (listOfNotNull(unit.takeIf { it in processorUnits }) + listed).distinct()
            dependencies {
                for (w in wanted) {
                    val flavour = if (usesMine(w)) "mine" else "solution"
                    "ksp${unit.cap()}"(project(":$lab")) { capabilities { requireCapability(capability(w, flavour)) } }
                }
            }

            // processor options for this unit only: src/<unit>/ksp.properties (key=value lines)
            val optionsFile = file("src/$unit/ksp.properties")
            if (optionsFile.isFile) {
                val options = java.util.Properties().apply { optionsFile.reader().use(::load) }
                    .entries.associate { (k, v) -> k.toString() to v.toString() }
                tasks.withType<com.google.devtools.ksp.gradle.KspAATask>().configureEach {
                    if (name == "ksp${unit.cap()}Kotlin") kspConfig.processorOptions.putAll(options)
                }
            }

            // the app's tests and demos see every unit's classes (generated ones included)
            sourceSets["test"].compileClasspath += set.output
            sourceSets["test"].runtimeClasspath += set.output + set.runtimeClasspath
            tasks.named<JavaExec>("demo") { classpath += set.runtimeClasspath }
        }

        // the app has no reference answers of its own: solutionTest runs the same tests as test, so
        // ./gradlew solutionTest (CI) proves the solution processors work in a real build
        tasks.named<Test>("solutionTest") {
            testClassesDirs = sourceSets["test"].output.classesDirs
            classpath = sourceSets["test"].runtimeClasspath
        }
    }
}

processorLab("ksp")
processorLab("injector")
