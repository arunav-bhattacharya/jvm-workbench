package workbench.ksp.l06

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.ClassKind
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.google.devtools.ksp.symbol.KSValueParameter
import com.google.devtools.ksp.validate
import com.squareup.kotlinpoet.ClassName
import com.squareup.kotlinpoet.CodeBlock
import com.squareup.kotlinpoet.FileSpec
import com.squareup.kotlinpoet.FunSpec
import com.squareup.kotlinpoet.KModifier
import com.squareup.kotlinpoet.PropertySpec
import com.squareup.kotlinpoet.STRING
import com.squareup.kotlinpoet.TypeSpec
import com.squareup.kotlinpoet.joinToCode
import com.squareup.kotlinpoet.ksp.addOriginatingKSFile
import com.squareup.kotlinpoet.ksp.toClassName
import com.squareup.kotlinpoet.ksp.toTypeName
import com.squareup.kotlinpoet.ksp.writeTo
import workbench.ksp.annotations.Inventory
import workbench.ksp.annotations.Moving

// Lesson 6, reference answer: the @Moving processor. Its output, a receipt, carries @Inventory, so the card
// processor (InventoryProcessor.kt, given) writes a card for it one round later. A class whose label mentions a receipt
// that doesn't exist yet is set aside until it does, and anything still set aside at the end is reported.

/** KSP creates the processor through this provider. Registered in workbench/ksp/l06/SymbolProcessorProvider. */
class ReceiptProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        ReceiptProcessor(environment.codeGenerator, environment.logger)
}

/**
 * For each class annotated [Moving], generates `<Name>Receipt.kt`: a data class `<Name>Receipt` annotated
 * [Inventory], with the class's constructor properties plus `signedBy`, and `fun <Name>.receipt(signedBy)`.
 */
class ReceiptProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
) : SymbolProcessor {

    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    // Given: KSP creates this processor once and calls process() once per round, so fields live across rounds.
    /** The number of the round being processed: 1, 2, 3... */
    private var round = 0

    /** The symbols this processor set aside in the round that just ran. */
    private var waiting: List<KSAnnotated> = emptyList()

    // Given code: while the lab is unfinished these log a warning and do nothing,
    // so a real build with -Pmine still runs.
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        processReceipts(resolver)
    } catch (e: NotImplementedError) {
        logger.warn("l06 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        emptyList()
    }

    override fun finish() = try {
        reportLeftovers()
    } catch (e: NotImplementedError) {
        logger.warn("l06 not done yet: ${e.message?.substringAfter("not implemented: ")}")
    }

    /**
     * One round, the five moves plus the round bookkeeping:
     * - Count the round (`round++`).
     * 1. Find the symbols annotated @Moving. In round 2 and later, these are the symbols from the files written in the
     *    round before, plus the symbols set aside in the round before.
     * - Split them with `validate(apiFeatures = apiFeatures)`. A receipt copies its class's property types, so a class
     *   whose types can't be resolved yet must wait.
     * 2. Check each valid one with [check], 3. Read and 4. Write: `receiptFile(cls).writeTo(codeGenerator, aggregating = false)`.
     * - Remember what was set aside in [waiting], log the round, and return the set-aside symbols so KSP offers them
     *   again next round. The log line, exactly:
     *   `[receipts] round 1: wrote [LampReceipt], set aside [Van]`
     * 5. Prove: the tests, then `./gradlew :ksp:app:kspL06Kotlin`.
     */
    fun processReceipts(resolver: Resolver): List<KSAnnotated> {
        round++
        val symbols = resolver.getSymbolsWithAnnotation(Moving::class.qualifiedName!!).toList()
        val (ready, later) = symbols.partition { it.validate(apiFeatures = apiFeatures) }
        val written = mutableListOf<String>()
        for (symbol in ready) {
            if (!check(symbol)) continue
            val file = receiptFile(symbol as KSClassDeclaration)
            file.writeTo(codeGenerator, aggregating = false)
            written += file.name
        }
        waiting = later
        logger.warn("[receipts] round $round: wrote $written, set aside ${later.map(::nameOf)}")
        return later
    }

    /**
     * After the last round, KSP calls finish(). KSP 2.3.14 says nothing about symbols that were still set aside, so
     * this processor says it: log `[receipts] finish() after 4 rounds` (use [rounds] for "1 round"), then one error
     * on each symbol still in [waiting], with [missingTypes] naming what it was waiting for:
     * `TrailerReceipt was never written: Trailer still needed PianoReceipt when processing ended after 1 round. Check the spelling, or the annotation that should generate PianoReceipt.`
     */
    fun reportLeftovers() {
        logger.warn("[receipts] finish() after ${rounds(round)}")
        for (symbol in waiting) {
            val cls = symbol as KSClassDeclaration
            val missing = missingTypes(cls).joinToString(", ")
            logger.error(
                "${receiptName(cls).simpleName} was never written: ${nameOf(cls)} still needed $missing " +
                    "when processing ended after ${rounds(round)}. Check the spelling, or the annotation that should generate $missing.",
                cls,
            )
        }
    }

    /** Given: 2. Check. A receipt copies the primary constructor's properties, so it needs a class that has one. */
    fun check(symbol: KSAnnotated): Boolean {
        if (symbol is KSClassDeclaration && symbol.classKind == ClassKind.CLASS && symbol.primaryConstructor != null) return true
        logger.error("@Moving needs a class with a primary constructor, so that the receipt can copy its properties", symbol)
        return false
    }
}

/** Given: a symbol's short name for log lines, `Van` for a class. */
fun nameOf(symbol: KSAnnotated): String = (symbol as? KSClassDeclaration)?.simpleName?.asString() ?: symbol.toString()

/** Given: `LampReceipt` for `Lamp`, in the same package. */
fun receiptName(cls: KSClassDeclaration): ClassName =
    ClassName(cls.packageName.asString(), cls.simpleName.asString() + "Receipt")

/** Given: the primary constructor parameters that are properties (`val` or `var`): a receipt copies those. */
fun copiedProperties(cls: KSClassDeclaration): List<KSValueParameter> =
    cls.primaryConstructor!!.parameters.filter { it.isVal || it.isVar }

/**
 * Given: the types in a class's constructor that can't be resolved, for example `[PianoReceipt]`. KSP 2.3.14 prints
 * such a type as `<ERROR TYPE: PianoReceipt>`; this keeps the name inside.
 */
fun missingTypes(cls: KSClassDeclaration): List<String> =
    cls.primaryConstructor?.parameters.orEmpty().map { it.type.resolve() }.filter { it.isError }
        .map { it.toString().removePrefix("<ERROR TYPE: ").removeSuffix(">") }

/** Given: `1 round`, `4 rounds`. */
fun rounds(n: Int): String = if (n == 1) "1 round" else "$n rounds"

/**
 * Given: 3. Read and 4. Write, with KotlinPoet as in lesson 4. For `@Moving data class Lamp(val name: String, ...)`:
 * ```
 * @Inventory
 * public data class LampReceipt(
 *   public val name: String,
 *   ...
 *   public val signedBy: String,
 * )
 *
 * public fun Lamp.receipt(signedBy: String): LampReceipt = LampReceipt(name, bulbs, shade, signedBy)
 * ```
 */
fun receiptFile(cls: KSClassDeclaration): FileSpec {
    val receipt = receiptName(cls)
    val copied = copiedProperties(cls)
    val constructor = FunSpec.constructorBuilder()
    val type = TypeSpec.classBuilder(receipt)
        .addModifiers(KModifier.DATA)
        .addAnnotation(Inventory::class)
        .addOriginatingKSFile(cls.containingFile!!)
    for (param in copied) {
        val name = param.name!!.asString()
        val typeName = param.type.toTypeName()      // throws if the type can't be resolved: validate() first
        constructor.addParameter(name, typeName)
        type.addProperty(PropertySpec.builder(name, typeName).initializer("%N", name).build())
    }
    constructor.addParameter("signedBy", STRING)
    type.addProperty(PropertySpec.builder("signedBy", STRING).initializer("signedBy").build())
    type.primaryConstructor(constructor.build())

    val arguments = (copied.map { CodeBlock.of("%N", it.name!!.asString()) } + CodeBlock.of("signedBy")).joinToCode()
    val receiptOf = FunSpec.builder("receipt")
        .receiver(cls.toClassName())
        .addParameter("signedBy", STRING)
        .returns(receipt)
        .addStatement("return %T(%L)", receipt, arguments)
        .addOriginatingKSFile(cls.containingFile!!)
        .build()
    return FileSpec.builder(receipt)
        .addFileComment("Generated by ReceiptProcessor from %L. Do not edit.", cls.simpleName.asString())
        .addType(type.build())
        .addFunction(receiptOf)
        .build()
}
