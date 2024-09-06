import React from 'react';

function NotFound() {
    return (
        <div className="flex items-start justify-center h-screen bg-slate-900 pt-20 md:pt-32">
            <div className="text-center">
                <h1 className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-green-400 mb-4">
                    404
                </h1>
                <p className="text-2xl text-slate-300">
                    Stock Not Found
                </p>
                <p className="text-slate-400 mt-2">
                    Sorry, the stock you're looking for doesn't exist.
                </p>
            </div>
        </div>
    );
}

export default NotFound;
