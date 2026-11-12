Name:		gradle-idea-ext
Version:	1.3
Release:	1
Summary:	Gradle plugin that extends the IDEA project model
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/JetBrains/gradle-idea-ext-plugin
# Tag v1.3. The Gradle wrapper jar is not in this archive.
# Groovy sources are compiled with FileSystemCompiler. The one Kotlin
# file is compiled with kotlinc. The Gradle tool is not invoked.
Source0:	gradle-idea-ext-%{version}.tar.gz
Patch0:		gradle-idea-ext-gradle8.patch

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	gradle
BuildRequires:	apache-groovy
BuildRequires:	antlr4
BuildRequires:	objectweb-asm
BuildRequires:	picocli
BuildRequires:	jansi
BuildRequires:	kotlin
BuildRequires:	kotlin-libs
BuildRequires:	mvn(javax.inject:javax.inject)
BuildRequires:	mvn(com.google.code.gson:gson)
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
Gradle plugin id org.jetbrains.gradle.plugin.idea-ext. The catalog
pin is gradle.plugin.org.jetbrains.gradle.plugin.idea-ext:gradle-idea-ext
1.3. Groovy sources are compiled with Groovy's FileSystemCompiler
from apache-groovy 4.0.33. IdeaModelUtils.kt is compiled with
kotlinc 2.0.21 on JDK 21. Gson is the system jar. Applying the
plugin and setting the compiler resource pattern makes
ProjectSettings render that pattern as JSON. Gradle supplies
kotlin-stdlib when the Kotlin DSL helpers run.

%prep
%autosetup -n gradle-idea-ext-plugin-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find src/main/groovy -name '*.groovy' | sort > groovy.list
find src/main/kotlin -name '*.kt' | sort > kotlin.list
test "$(wc -l < groovy.list)" -eq 22
test "$(wc -l < kotlin.list)" -eq 1
grep -F -q 'CollectionCallbackActionDecorator.NOOP' src/main/groovy/org/jetbrains/gradle/ext/internal/DefaultRunConfigurationContainer.groovy
grep -F -q 'return map as Map<String, ?>' src/main/groovy/org/jetbrains/gradle/ext/Copyright.groovy
if grep -q 'void buildStarted' src/main/groovy/org/jetbrains/gradle/ext/IdeaFilesProcessor.groovy; then
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CP=$(find %{_datadir}/gradle -name '*.jar' | sort | paste -sd: -)
for extra in \
	%{_javadir}/atinject.jar \
	%{_javadir}/apache-groovy.jar \
	%{_javadir}/gson.jar \
	%{_javadir}/kotlin-stdlib.jar \
	%{_javadir}/kotlin-reflect.jar
do
	test -s "$extra"
	CP="$CP:$extra"
done
mkdir -p classes
GROOVY_CP=%{_javadir}/apache-groovy.jar
for extra in \
	%{_javadir}/antlr4-runtime.jar \
	%{_javadir}/asm.jar \
	%{_javadir}/asm-commons.jar \
	%{_javadir}/asm-tree.jar \
	%{_javadir}/asm-util.jar \
	%{_javadir}/picocli.jar \
	/usr/lib/java/jansi/jansi.jar
do
	test -s "$extra"
	GROOVY_CP="$GROOVY_CP:$extra"
done
GROOVY_CP="$GROOVY_CP:$CP"
java -Dgroovy.target.bytecode=11 -cp "$GROOVY_CP" org.codehaus.groovy.tools.FileSystemCompiler \
	--classpath "$GROOVY_CP" -d classes @groovy.list
kotlinc -jvm-target 11 -language-version 2.0 -api-version 2.0 -cp "$CP:classes" -d classes $(sort kotlin.list)
test "$(find classes -name '*.class' | wc -l)" -eq 164
for cls in \
	org.jetbrains.gradle.ext.IdeaExtPlugin \
	org.jetbrains.gradle.ext.ProjectSettings \
	org.jetbrains.gradle.ext.IdeaModelUtilsKt
do
	javap -v -classpath classes "$cls" | grep -F -q 'major version: 55'
done
mkdir -p classes/META-INF/gradle-plugins
printf '%s\n' 'implementation-class=org.jetbrains.gradle.ext.IdeaExtPlugin' \
	> classes/META-INF/gradle-plugins/org.jetbrains.gradle.plugin.idea-ext.properties
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: org.jetbrains.gradle.ext' > manifest.mf
jar cfm gradle-idea-ext.jar manifest.mf -C classes .
jar i gradle-idea-ext.jar
jar tf gradle-idea-ext.jar | grep -F -q 'org/jetbrains/gradle/ext/IdeaExtPlugin.class'
jar tf gradle-idea-ext.jar | grep -F -q 'org/jetbrains/gradle/ext/IdeaModelUtilsKt.class'
jar tf gradle-idea-ext.jar | grep -F -q 'META-INF/gradle-plugins/org.jetbrains.gradle.plugin.idea-ext.properties'
desc=$(jar --describe-module --file gradle-idea-ext.jar)
printf '%s\n' "$desc" | grep -F -q 'org.jetbrains.gradle.ext'
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	printf '%s\n' "$desc"
	exit 1
fi

cat > gradle-idea-ext.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>gradle.plugin.org.jetbrains.gradle.plugin.idea-ext</groupId>
  <artifactId>gradle-idea-ext</artifactId>
  <version>%{version}</version>
  <name>gradle-idea-ext</name>
  <description>Extends the Gradle IDEA DSL with code style, facets, and run configurations.</description>
  <url>https://github.com/JetBrains/gradle-idea-ext-plugin</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.apache.groovy</groupId>
      <artifactId>groovy</artifactId>
      <version>4.0.33</version>
    </dependency>
    <dependency>
      <groupId>com.google.code.gson</groupId>
      <artifactId>gson</artifactId>
      <version>2.15.0</version>
    </dependency>
    <dependency>
      <groupId>javax.inject</groupId>
      <artifactId>javax.inject</artifactId>
      <version>1.0.5</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact gradle-idea-ext.pom:gradle-idea-ext.jar \
	--file-name gradle-idea-ext \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/gradle.plugin.org.jetbrains.gradle.plugin.idea-ext/gradle-idea-ext.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "gradle-idea-ext"' "$idx"
test -s %{buildroot}%{_javadir}/gradle-idea-ext.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/gradle-idea-ext.jar
test -s "$JAR"
CP=$(find %{_datadir}/gradle -name '*.jar' | sort | paste -sd: -)
for extra in \
	%{_javadir}/atinject.jar \
	%{_javadir}/apache-groovy.jar \
	%{_javadir}/gson.jar \
	%{_javadir}/kotlin-stdlib.jar \
	%{_javadir}/kotlin-reflect.jar
do
	test -s "$extra"
	CP="$CP:$extra"
done
mkdir -p check
cat > check/Smoke.java << 'EOF'
import org.gradle.api.Project;
import org.gradle.api.plugins.ExtensionAware;
import org.gradle.plugins.ide.idea.model.IdeaModel;
import org.gradle.testfixtures.ProjectBuilder;
import org.jetbrains.gradle.ext.IdeaCompilerConfiguration;
import org.jetbrains.gradle.ext.IdeaExtPlugin;
import org.jetbrains.gradle.ext.ProjectSettings;

public class Smoke {
	public static void main(String[] args) {
		int code = 1;
		try {
			Project project = ProjectBuilder.builder().build();
			project.getPluginManager().apply(IdeaExtPlugin.class);
			IdeaModel idea = project.getExtensions().getByType(IdeaModel.class);
			ProjectSettings settings = (ProjectSettings) ((ExtensionAware) idea.getProject()).getExtensions().getByName("settings");
			IdeaCompilerConfiguration compiler = (IdeaCompilerConfiguration) ((ExtensionAware) settings).getExtensions().getByName("compiler");
			compiler.setResourcePatterns("!*.java;!*.class");
			String json = settings.toString();
			if (json == null || !json.contains("\"resourcePatterns\":\"!*.java;!*.class\"")) {
				throw new AssertionError(json);
			}
			System.out.println(args[0] + " " + json);
			code = 0;
		} catch (Throwable t) {
			t.printStackTrace();
		}
		Runtime.getRuntime().halt(code);
	}
}
EOF
javac -encoding UTF-8 --release 11 -Xlint:-options -proc:none -cp "$JAR:$CP" -d check check/Smoke.java
"$JAVA_HOME/bin/java" \
	--add-opens=java.base/java.lang=ALL-UNNAMED \
	--add-opens=java.base/java.lang.invoke=ALL-UNNAMED \
	--add-opens=java.base/java.util=ALL-UNNAMED \
	--add-opens=java.prefs/java.util.prefs=ALL-UNNAMED \
	--add-opens=java.base/java.nio.charset=ALL-UNNAMED \
	--add-opens=java.base/java.net=ALL-UNNAMED \
	--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED \
	--add-opens=java.xml/javax.xml.namespace=ALL-UNNAMED \
	--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED \
	--add-exports=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED \
	-cp "check:$JAR:$CP" Smoke idea_ext_ok > check/out.txt
cat check/out.txt
grep -F -qx 'idea_ext_ok {"compiler":{"resourcePatterns":"!*.java;!*.class"}}' check/out.txt

%files -f .mfiles
%doc README.md
%license LICENSE.txt
