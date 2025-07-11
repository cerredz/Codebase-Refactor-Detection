def get_non_coding_files():
    NON_CODING_EXTENSIONS = set([
        # Document files
        '.txt', '.md', '.pdf', '.doc', '.docx', '.rtf', '.odt', '.pages',
        
        # Image files  
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.tiff', '.tif', '.webp',
        '.raw', '.cr2', '.nef', '.orf', '.sr2', '.psd', '.ai', '.eps',
        
        # Video files
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp',
        '.ogv', '.f4v', '.asf', '.rm', '.rmvb', '.vob', '.ts', '.mts',
        
        # Audio files
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus',
        '.amr', '.aiff', '.au', '.ra', '.ac3', '.dts',
        
        # Archive files
        '.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', '.xz', '.lzma', '.z',
        '.cab', '.iso', '.dmg', '.deb', '.rpm', '.msi', '.pkg',
        
        # Binary executable files
        '.exe', '.dll', '.so', '.dylib', '.app', '.deb', '.rpm', '.msi',
        '.bin', '.run', '.bundle', '.pkg', '.dmg',
        
        # Database files
        '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.dbf', '.frm', '.myd', '.myi',
        
        # Font files
        '.ttf', '.otf', '.woff', '.woff2', '.eot', '.pfb', '.pfm', '.afm',
        
        # Log and temporary files
        '.log', '.tmp', '.temp', '.cache', '.bak', '.swp', '.swo', '.orig',
        '.pid', '.lock', '.DS_Store', '.Thumbs.db',
        
        # Configuration files (some might be coding-related, but often not)
        '.ini', '.cfg', '.conf', '.properties', '.plist', '.reg',
        
        # Compiled/generated files
        '.pyc', '.pyo', '.pyd', '.class', '.o', '.obj', '.lib', '.a', '.la',
        '.lo', '.slo', '.ko', '.mod', '.pch', '.gch', '.gcno', '.gcda',
        
        # IDE/Editor files
        '.suo', '.user', '.sln', '.vcxproj', '.vcproj', '.pbxproj', '.xcodeproj',
        '.workspace', '.project', '.classpath', '.settings', '.idea',
        
        # Version control files
        '.git', '.svn', '.hg', '.bzr',
        
        # Package management files (binary packages)
        '.gem', '.egg', '.whl', '.jar', '.war', '.ear', '.aar', '.apk',
        
        # Data files (might contain some coding-related ones, but generally data)
        '.csv', '.xlsx', '.xls', '.ods', '.tsv', '.dat', '.data', '.backup',
        
        # Certificate and key files
        '.pem', '.crt', '.cer', '.der', '.p7b', '.p7c', '.p12', '.pfx', '.key',
        
        # Other binary/non-text files
        '.bin', '.hex', '.img', '.vhd', '.vmdk', '.qcow2', '.raw',
    ])

    return NON_CODING_EXTENSIONS