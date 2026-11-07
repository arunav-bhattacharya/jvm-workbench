// cap3 (labs/events): kotlin-reflect is used only by the tests, for PaymentEvent::class.sealedSubclasses
// (cap3-01) and Handler::class.typeParameters (cap3-02). The library itself needs only the standard
// library: KClass.cast, isInstance and Java reflection work without kotlin-reflect.
dependencies {
    testImplementation("org.jetbrains.kotlin:kotlin-reflect:2.4.21")
}
