plugins {
    id("java")
    id("com.gradleup.shadow") version("9.0.0-beta6")
}

group = "dev.badbird"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
    mavenLocal();
}

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.10.0"))
    testImplementation("org.junit.jupiter:junit-jupiter")

    val pi4jVersion = "2.8.0";
    implementation("io.javalin:javalin:5.6.1")
    implementation("com.pi4j:pi4j-core:$pi4jVersion")
    implementation("com.pi4j:pi4j-plugin-raspberrypi:$pi4jVersion")
    implementation("com.pi4j:pi4j-plugin-gpiod:$pi4jVersion")
//    implementation("com.pi4j:pi4j-plugin-pigpio:2.8.0")
    implementation("com.google.code.gson:gson:2.12.1")
}

tasks {
    test {
        useJUnitPlatform()
    }
}

tasks.named<com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar>("shadowJar") {
    archiveBaseName.set("ioserver")
    archiveClassifier.set("")
    archiveVersion.set("")
    manifest {
        attributes(mapOf("Main-Class" to "dev.badbird.Main"))
    }
}