tailwind.config = {
    theme: {
        extend: {
            colors: {
                parchment: {
                    DEFAULT: '#ede8df',
                    light: '#f7f4ef',
                    muted: '#f0ece4',
                    elevated: '#e6e0d5',
                },
                ink: {
                    DEFAULT: '#2c2824',
                    light: '#5a534a',
                    muted: '#8a8276',
                },
                'border-light': '#ddd6c8',
                'border-dark': '#c8bfb0',
                triage: {
                    red: '#c23b3b',
                    yellow: '#b8860b',
                    green: '#3d7a5e',
                    blue: '#4a6fa5',
                }
            },
            fontFamily: {
                mono: ['"SF Mono"', '"Fira Code"', '"Cascadia Code"', '"Source Code Pro"', 'Consolas', '"Courier New"', 'monospace'],
            }
        }
    }
}
