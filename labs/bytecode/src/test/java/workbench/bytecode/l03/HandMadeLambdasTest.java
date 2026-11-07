package workbench.bytecode.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodType;
import java.lang.reflect.Proxy;
import java.util.function.IntUnaryOperator;

import static org.assertj.core.api.Assertions.assertThat;

class HandMadeLambdasTest {

    @Test
    @DisplayName("adder() adds two amounts")
    void adderAdds() {
        assertThat(HandMadeLambdas.adder().applyAsInt(1_250, 30)).isEqualTo(1_280);
    }

    @Test
    @DisplayName("adder() is a hidden $$Lambda class, not a proxy, and the same object on every call")
    void adderIsALambda() {
        Object a = HandMadeLambdas.adder();
        assertThat(a.getClass().isHidden()).isTrue();
        assertThat(a.getClass().getName()).contains("$$Lambda");
        assertThat(Proxy.isProxyClass(a.getClass())).isFalse();
        assertThat(HandMadeLambdas.adder()).isSameAs(a);
    }

    @Test
    @DisplayName("plusFee(fee) adds the captured fee to each amount")
    void plusFeeCaptures() {
        assertThat(HandMadeLambdas.plusFee(30).applyAsInt(1_250)).isEqualTo(1_280);
        assertThat(HandMadeLambdas.plusFee(45).applyAsInt(1_250)).isEqualTo(1_295);
    }

    @Test
    @DisplayName("plusFee: one linked call site, so two fees give two objects of ONE class")
    void plusFeeLinksOnce() {
        IntUnaryOperator f30 = HandMadeLambdas.plusFee(30);
        IntUnaryOperator f45 = HandMadeLambdas.plusFee(45);
        assertThat(f30).isNotSameAs(f45);
        assertThat(f30.getClass()).isSameAs(f45.getClass());
        assertThat(f30.getClass().isHidden()).isTrue();
    }

    @Test
    @DisplayName("lengthOf() is String::length behind the erased Function.apply, with the int boxed")
    void lengthOf() {
        assertThat(HandMadeLambdas.lengthOf().apply("4111111111111111")).isEqualTo(16);
        assertThat(HandMadeLambdas.lengthOf().getClass().isHidden()).isTrue();
    }

    @Test
    @DisplayName("receipt() is a (long, String)String handle that fills the recipe")
    void receipt() throws Throwable {
        MethodHandle h = HandMadeLambdas.receipt();
        assertThat(h.type()).isEqualTo(MethodType.methodType(String.class, long.class, String.class));
        assertThat((String) h.invokeExact(1_250L, "Corner Coffee")).isEqualTo("paid 1250 to Corner Coffee");
    }
}
