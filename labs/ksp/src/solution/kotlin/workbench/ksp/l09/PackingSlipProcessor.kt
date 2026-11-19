package workbench.ksp.l09

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.Dependencies
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.ClassKind
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import workbench.ksp.annotations.Inventory
import workbench.ksp.annotations.Room

// Lesson 9: the KSP port of JavacPackingSlipProcessor.java (in src/main/java, same package). Same output, byte for
// byte: META-INF/movemate/packing-slip.txt with one line per @Inventory class. Port it one move at a time; each
// function below names the javac line it replaces.
//   ./gradlew :ksp:test --tests 'workbench.ksp.l09.*'
//   ./gradlew :ksp:app:kspL09Kotlin      then open app/build/generated/ksp/l09/resources/META-INF/movemate/

/** The processor option, read like `processingEnv.getOptions().getOrDefault("movemate.household", "MoveMate")`. */
const val HOUSEHOLD = "movemate.household"

/** KSP creates the processor through this provider (javac would call a public no-argument constructor instead). */
class PackingSlipProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        PackingSlipProcessor(environment.codeGenerator, environment.logger, environment.options)
}

class PackingSlipProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
    private val options: Map<String, String>,
) : SymbolProcessor {

    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    private var slipWritten = false

    // Given code: while the lab is unfinished this logs a warning and generates nothing,
    // so a real build with -Pmine=l09 still runs.
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        processSlip(resolver)
    } catch (e: NotImplementedError) {
        if (!slipWritten) logger.warn("l09 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        slipWritten = true // warn once: lesson 7's processor runs here too, so KSP may come back for a second round
        emptyList()
    }

    /** Given: the same steps, in the same order, as JavacPackingSlipProcessor.process. */
    fun processSlip(resolver: Resolver): List<KSAnnotated> {
        if (slipWritten) return emptyList()                           // javac: if (slipWritten || processingOver())
        val household = options[HOUSEHOLD] ?: "MoveMate"              // javac: getOptions().getOrDefault(...)
        val classes = findInventory(resolver).mapNotNull { checkKind(it, logger) }
            .sortedBy { it.simpleName.asString() }
        if (classes.isEmpty()) return emptyList()
        val lines = classes.map(::slipLine)
        val text = "# $household packing slip. Generated, do not edit.\n" + lines.joinToString("") { "$it\n" }
        codeGenerator.createNewFile(slipDependencies(classes), "META-INF/movemate", "packing-slip", "txt")
            .use { it.write(text.toByteArray()) }
        slipWritten = true
        return emptyList()                                            // javac returned false: claim nothing
    }
}

/** 1. Find. javac: `roundEnv.getElementsAnnotatedWith(Inventory.class)` */
fun findInventory(resolver: Resolver): List<KSAnnotated> =
    resolver.getSymbolsWithAnnotation(Inventory::class.qualifiedName!!).toList()

/**
 * 2. Check. javac: `if (element.getKind() != ElementKind.CLASS) messager.printMessage(Diagnostic.Kind.ERROR, ..., element)`.
 * Returns the class, or null after an error on the symbol. The words match javac's `kindWords`, plus one kind
 * javac never sees: a Kotlin object.
 */
fun checkKind(symbol: KSAnnotated, logger: KSPLogger): KSClassDeclaration? {
    if (symbol is KSClassDeclaration && symbol.classKind == ClassKind.CLASS) return symbol
    val name = (symbol as? KSClassDeclaration)?.simpleName?.asString() ?: symbol.toString()
    val words = when ((symbol as? KSClassDeclaration)?.classKind) {
        ClassKind.INTERFACE -> "an interface"
        ClassKind.ENUM_CLASS -> "an enum"
        ClassKind.ANNOTATION_CLASS -> "an annotation"
        ClassKind.OBJECT -> "an object"
        else -> "not a class"
    }
    logger.error("@Inventory goes on a class, but $name is $words", symbol)
    return null
}

/**
 * 3. Read. javac: the fields in source order (`ElementFilter.fieldsIn(...)`), and `type.getAnnotation(Room.class)`.
 * KSP: the primary constructor's properties in order, and @Room's `name` argument from the KSAnnotation.
 * Returns `Lamp [living room]: name, bulbs, shade`.
 */
fun slipLine(cls: KSClassDeclaration): String {
    val room = cls.annotations
        .firstOrNull { it.shortName.asString() == "Room" &&                       // cheap: the word on the note
            it.annotationType.resolve().declaration.qualifiedName?.asString() == Room::class.qualifiedName } // exact
        ?.arguments?.firstOrNull { it.name?.asString() == "name" }?.value as String?
    val names = cls.primaryConstructor?.parameters.orEmpty().filter { it.isVal || it.isVar }.map { it.name!!.asString() }
    return "${cls.simpleName.asString()} [${room ?: "no room"}]: ${names.joinToString(", ")}"
}

/**
 * 4. Write, the Dependencies. javac: `filer.createResource(CLASS_OUTPUT, "", "META-INF/movemate/packing-slip.txt",
 * originatingElements)`, and `aggregating` in Gradle's incremental.annotation.processors file. KSP puts that
 * category on the output itself: aggregating, from the file of every class on the slip.
 */
fun slipDependencies(classes: List<KSClassDeclaration>): Dependencies =
    Dependencies(aggregating = true, *classes.mapNotNull { it.containingFile }.distinct().toTypedArray())
