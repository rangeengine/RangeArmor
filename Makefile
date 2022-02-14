ifdef OS
	TARGET = i686-pc-windows-gnu
	DELETE = del /Q
	COPY = copy /-Y
	EXT = .exe
	END = &&
	SOURCE_EXE = ".\target\$(TARGET)\release\bgarmor$(EXT)"
	TARGET_EXE = "..\..\BGArmor$(EXT)"
	UPX = REM
else
	TARGET = i686-unknown-linux-gnu
	DELETE = rm -f
	COPY = cp -f
	EXT =
	END = ;
	SOURCE_EXE = "./target/$(TARGET)/release/bgarmor$(EXT)"
	TARGET_EXE = "../../BGArmor$(EXT)"
	UPX = upx -5
endif

build:
	cd "./source/launcher/" $(END) \
	$(DELETE) $(TARGET_EXE) $(END) \
	cargo build --target=$(TARGET) --release $(END) \
	$(COPY) $(SOURCE_EXE) $(TARGET_EXE) $(END) \
	$(UPX) $(TARGET_EXE)
